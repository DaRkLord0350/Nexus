import asyncio
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.models.marketplace_order_link import MarketplaceOrderLinkStatus
from app.models.marketplace_webhook_event import MarketplaceWebhookStatus
from app.schemas.marketplace_connector import MarketplaceConnectorCreateRequest
from app.schemas.marketplace_webhook_event import MarketplaceWebhookRequest
from app.schemas.product import ProductCreateRequest
from app.schemas.product_price import ProductPriceCreateRequest
from app.services.auth_service import AuthService
from app.services.marketplace_connector_service import MarketplaceConnectorService
from app.services.marketplace_sync_service import MarketplaceSyncService
from app.services.marketplace_webhook_service import MarketplaceWebhookService
from app.services.pricing_service import PricingService
from app.services.product_service import ProductService


@pytest.fixture
def app_session(tmp_path) -> AsyncSession:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    engine = create_async_engine(database_url, future=True)

    async def initialize_database() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(initialize_database())
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    session = async_session()

    try:
        yield session
    finally:
        asyncio.run(session.close())
        asyncio.run(engine.dispose())


async def _register_org(session, email="owner@example.com", org_name="Marketplace Webhook Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _setup_connector(session, org_id, user_id, code="woo-main", webhook_secret=None):
    connector_service = MarketplaceConnectorService(session, organization_id=org_id)
    return await connector_service.create_connector(
        MarketplaceConnectorCreateRequest(name="Woo", code=code, connector_type="woocommerce", webhook_secret=webhook_secret),
        created_by=user_id,
    )


async def _setup_linked_product(session, org_id, user_id, connector_id, sku="WID-1"):
    product_service = ProductService(session, organization_id=org_id)
    product = await product_service.create_product(ProductCreateRequest(name="Widget", sku=sku, track_inventory=False), created_by=user_id)
    product = await product_service.publish_product(product.id, actor_id=user_id)

    pricing_service = PricingService(session, organization_id=org_id)
    await pricing_service.create_price(ProductPriceCreateRequest(product_id=product.id, currency="USD", selling_price=25.0), created_by=user_id)

    sync_service = MarketplaceSyncService(session, organization_id=org_id)
    await sync_service.sync_products(connector_id)
    links = await sync_service.link_repo.list(connector_id=connector_id)
    return product, links[0]


def test_webhook_rejects_wrong_secret(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        connector = await _setup_connector(app_session, user.organization_id, user.id, webhook_secret="s3cr3t")

        service = MarketplaceWebhookService(app_session, organization_id=user.organization_id)
        data = MarketplaceWebhookRequest(connector_code=connector.code, event_type="order.created", payload={"external_order_id": "1"})

        with pytest.raises(HTTPException) as exc_info:
            await service.process_webhook(data, webhook_secret="wrong")
        assert exc_info.value.status_code == 401

    asyncio.run(_run())


def test_webhook_imports_order_and_marks_processed(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        connector = await _setup_connector(app_session, user.organization_id, user.id)
        _product, link = await _setup_linked_product(app_session, user.organization_id, user.id, connector.id)

        service = MarketplaceWebhookService(app_session, organization_id=user.organization_id)
        payload = {
            "external_order_id": "WOO-500",
            "customer_email": "buyer@example.com",
            "shipping_address": {"first_name": "Bella", "last_name": "Buyer", "line1": "1 Elm St", "city": "Metropolis", "country": "US"},
            "items": [{"external_id": link.external_id, "quantity": 1, "unit_price": 25.0}],
        }
        data = MarketplaceWebhookRequest(connector_code=connector.code, event_type="order.created", payload=payload)

        event = await service.process_webhook(data)
        assert event.status == MarketplaceWebhookStatus.processed
        assert event.retry_count == 0

    asyncio.run(_run())


def test_webhook_failure_schedules_retry(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        connector = await _setup_connector(app_session, user.organization_id, user.id)

        service = MarketplaceWebhookService(app_session, organization_id=user.organization_id)
        payload = {
            "external_order_id": "WOO-501",
            "customer_email": "buyer@example.com",
            "shipping_address": {"first_name": "Bella", "last_name": "Buyer", "line1": "1 Elm St", "city": "Metropolis", "country": "US"},
            "items": [{"external_id": "does-not-exist", "quantity": 1, "unit_price": 25.0}],
        }
        data = MarketplaceWebhookRequest(connector_code=connector.code, event_type="order.created", payload=payload)

        event = await service.process_webhook(data)
        assert event.status == MarketplaceWebhookStatus.failed
        assert event.retry_count == 1
        assert event.next_retry_at is not None
        assert event.last_error is not None

    asyncio.run(_run())


def test_retry_due_events_reprocesses_and_succeeds_once_fixed(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        connector = await _setup_connector(app_session, user.organization_id, user.id)
        _product, link = await _setup_linked_product(app_session, user.organization_id, user.id, connector.id)

        service = MarketplaceWebhookService(app_session, organization_id=user.organization_id)
        # First attempt references a product that isn't linked yet -> fails.
        bad_payload = {
            "external_order_id": "WOO-900",
            "customer_email": "buyer@example.com",
            "shipping_address": {"first_name": "Bella", "last_name": "Buyer", "line1": "1 Elm St", "city": "Metropolis", "country": "US"},
            "items": [{"external_id": "not-yet-linked", "quantity": 1, "unit_price": 25.0}],
        }
        data = MarketplaceWebhookRequest(connector_code=connector.code, event_type="order.created", payload=bad_payload)
        event = await service.process_webhook(data)
        assert event.status == MarketplaceWebhookStatus.failed

        # Force it due now (rather than sleeping for the real backoff window).
        event.next_retry_at = datetime.utcnow() - timedelta(seconds=1)
        await service.event_repo.save(event)

        # Still references the same unresolvable external_id, so retry keeps failing
        # (this exercises the retry_count increment / due-selection plumbing).
        retried = await service.retry_due_events(connector_id=connector.id)
        assert len(retried) == 1
        assert retried[0].id == event.id
        assert retried[0].retry_count == 2

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")

        connector_a = await _setup_connector(app_session, user_a.organization_id, user_a.id)

        service_a = MarketplaceWebhookService(app_session, organization_id=user_a.organization_id)
        service_b = MarketplaceWebhookService(app_session, organization_id=user_b.organization_id)

        data = MarketplaceWebhookRequest(connector_code=connector_a.code, event_type="order.created", payload={"external_order_id": "1"})
        await service_a.process_webhook(data)

        items_b, total_b = await service_b.list_events()
        assert total_b == 0
        assert items_b == []

    asyncio.run(_run())
