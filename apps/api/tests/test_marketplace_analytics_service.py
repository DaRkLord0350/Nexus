import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.marketplace_connector import MarketplaceConnectorCreateRequest
from app.schemas.product import ProductCreateRequest
from app.schemas.product_price import ProductPriceCreateRequest
from app.services.auth_service import AuthService
from app.services.marketplace_analytics_service import MarketplaceAnalyticsService
from app.services.marketplace_connector_service import MarketplaceConnectorService
from app.services.marketplace_sync_service import MarketplaceSyncService
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


async def _register_org(session, email="owner@example.com", org_name="Marketplace Analytics Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


def test_dashboard_reflects_sync_and_order_activity(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)

        connector_service = MarketplaceConnectorService(app_session, organization_id=user.organization_id)
        connector = await connector_service.create_connector(MarketplaceConnectorCreateRequest(name="Woo", code="woo", connector_type="woocommerce"), created_by=user.id)

        product_service = ProductService(app_session, organization_id=user.organization_id)
        product = await product_service.create_product(ProductCreateRequest(name="Widget", sku="WID-1", track_inventory=False), created_by=user.id)
        product = await product_service.publish_product(product.id, actor_id=user.id)
        pricing_service = PricingService(app_session, organization_id=user.organization_id)
        await pricing_service.create_price(ProductPriceCreateRequest(product_id=product.id, currency="USD", selling_price=25.0), created_by=user.id)

        sync_service = MarketplaceSyncService(app_session, organization_id=user.organization_id)
        await sync_service.sync_products(connector.id)
        links = await sync_service.link_repo.list(connector_id=connector.id)

        payload = {
            "external_order_id": "WOO-1",
            "customer_email": "buyer@example.com",
            "shipping_address": {"first_name": "Bella", "last_name": "Buyer", "line1": "1 Elm St", "city": "Metropolis", "country": "US"},
            "items": [{"external_id": links[0].external_id, "quantity": 2, "unit_price": 25.0}],
        }
        await sync_service.import_order_payload(connector, payload)

        analytics_service = MarketplaceAnalyticsService(app_session, organization_id=user.organization_id)
        dashboard = await analytics_service.get_dashboard()

        assert dashboard["summary"]["total_syncs"] == 1
        assert dashboard["summary"]["sync_success_rate"] == 100.0
        assert dashboard["summary"]["total_orders_imported"] == 1
        assert dashboard["summary"]["total_revenue_imported"] == 50.0

        assert len(dashboard["connectors"]) == 1
        stats = dashboard["connectors"][0]
        assert stats["marketplace_connector_id"] == connector.id
        assert stats["orders_imported"] == 1
        assert stats["revenue_imported"] == 50.0
        assert stats["products_linked"] == 1

    asyncio.run(_run())


def test_dashboard_empty_state(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        analytics_service = MarketplaceAnalyticsService(app_session, organization_id=user.organization_id)
        dashboard = await analytics_service.get_dashboard()

        assert dashboard["summary"]["total_syncs"] == 0
        assert dashboard["summary"]["sync_success_rate"] == 0.0
        assert dashboard["connectors"] == []

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")

        connector_service = MarketplaceConnectorService(app_session, organization_id=user_a.organization_id)
        connector = await connector_service.create_connector(MarketplaceConnectorCreateRequest(name="Woo", code="woo"), created_by=user_a.id)
        sync_service = MarketplaceSyncService(app_session, organization_id=user_a.organization_id)
        await sync_service.sync_products(connector.id)

        analytics_service_b = MarketplaceAnalyticsService(app_session, organization_id=user_b.organization_id)
        dashboard_b = await analytics_service_b.get_dashboard()
        assert dashboard_b["connectors"] == []
        assert dashboard_b["summary"]["total_syncs"] == 0

    asyncio.run(_run())
