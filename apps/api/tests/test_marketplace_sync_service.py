import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.models.marketplace_order_link import MarketplaceOrderLinkStatus
from app.models.marketplace_product_link import MarketplaceLinkStatus
from app.models.marketplace_sync_log import MarketplaceSyncStatus
from app.schemas.marketplace_connector import MarketplaceConnectorCreateRequest
from app.schemas.product import ProductCreateRequest
from app.schemas.product_price import ProductPriceCreateRequest
from app.services.auth_service import AuthService
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


async def _register_org(session, email="owner@example.com", org_name="Marketplace Sync Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _setup_connector(session, org_id, user_id, code="woo-main"):
    connector_service = MarketplaceConnectorService(session, organization_id=org_id)
    return await connector_service.create_connector(MarketplaceConnectorCreateRequest(name="Woo", code=code, connector_type="woocommerce"), created_by=user_id)


async def _setup_product(session, org_id, user_id, sku="WID-1", price=25.0):
    product_service = ProductService(session, organization_id=org_id)
    product = await product_service.create_product(ProductCreateRequest(name="Widget", sku=sku, track_inventory=False), created_by=user_id)
    product = await product_service.publish_product(product.id, actor_id=user_id)

    pricing_service = PricingService(session, organization_id=org_id)
    await pricing_service.create_price(ProductPriceCreateRequest(product_id=product.id, currency="USD", selling_price=price), created_by=user_id)
    return product


def test_sync_products_creates_links(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        connector = await _setup_connector(app_session, user.organization_id, user.id)
        product = await _setup_product(app_session, user.organization_id, user.id)

        service = MarketplaceSyncService(app_session, organization_id=user.organization_id)
        log = await service.sync_products(connector.id)

        assert log.status == MarketplaceSyncStatus.success
        assert log.items_processed == 1
        assert log.items_succeeded == 1

        links = await service.link_repo.list(connector_id=connector.id)
        assert len(links) == 1
        assert links[0].product_id == product.id
        assert links[0].sync_status == MarketplaceLinkStatus.synced
        assert links[0].external_id is not None

    asyncio.run(_run())


def test_sync_prices_requires_existing_link(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        connector = await _setup_connector(app_session, user.organization_id, user.id)
        await _setup_product(app_session, user.organization_id, user.id, price=42.5)

        service = MarketplaceSyncService(app_session, organization_id=user.organization_id)
        await service.sync_products(connector.id)
        log = await service.sync_prices(connector.id)

        assert log.status == MarketplaceSyncStatus.success
        assert log.items_succeeded == 1

        links = await service.link_repo.list(connector_id=connector.id)
        assert links[0].last_synced_price == 42.5

    asyncio.run(_run())


def test_sync_inventory_sums_quantity(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        connector = await _setup_connector(app_session, user.organization_id, user.id)
        product = await _setup_product(app_session, user.organization_id, user.id)

        from app.models.inventory import Inventory
        from app.schemas.warehouse import WarehouseCreateRequest
        from app.services.warehouse_service import WarehouseService

        warehouse_service = WarehouseService(app_session, organization_id=user.organization_id)
        warehouse = await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Main", code="MAIN", is_default=True), created_by=user.id)

        inventory = Inventory(product_id=product.id, warehouse_id=warehouse.id, quantity_available=50)
        inventory.organization_id = user.organization_id
        app_session.add(inventory)
        await app_session.commit()

        service = MarketplaceSyncService(app_session, organization_id=user.organization_id)
        await service.sync_products(connector.id)
        log = await service.sync_inventory(connector.id)

        assert log.items_succeeded == 1
        links = await service.link_repo.list(connector_id=connector.id)
        assert links[0].last_synced_quantity == 50

    asyncio.run(_run())


def test_import_order_payload_creates_order(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        connector = await _setup_connector(app_session, user.organization_id, user.id)
        product = await _setup_product(app_session, user.organization_id, user.id, sku="WID-1")

        service = MarketplaceSyncService(app_session, organization_id=user.organization_id)
        await service.sync_products(connector.id)
        links = await service.link_repo.list(connector_id=connector.id)
        external_id = links[0].external_id

        payload = {
            "external_order_id": "WOO-1001",
            "external_order_number": "#1001",
            "currency": "USD",
            "customer_email": "buyer@example.com",
            "customer_first_name": "Bella",
            "customer_last_name": "Buyer",
            "shipping_address": {"first_name": "Bella", "last_name": "Buyer", "line1": "1 Elm St", "city": "Metropolis", "country": "US"},
            "items": [{"external_id": external_id, "quantity": 2, "unit_price": 25.0}],
        }

        link = await service.import_order_payload(connector, payload)
        assert link.status == MarketplaceOrderLinkStatus.imported
        assert link.order_id is not None

        # Re-importing the same external_order_id must be idempotent.
        link_again = await service.import_order_payload(connector, payload)
        assert link_again.id == link.id

    asyncio.run(_run())


def test_import_order_payload_fails_without_matching_product(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        connector = await _setup_connector(app_session, user.organization_id, user.id)

        payload = {
            "external_order_id": "WOO-2002",
            "customer_email": "buyer@example.com",
            "shipping_address": {"first_name": "Bella", "last_name": "Buyer", "line1": "1 Elm St", "city": "Metropolis", "country": "US"},
            "items": [{"external_id": "unknown-external-id", "quantity": 1, "unit_price": 10.0}],
        }

        service = MarketplaceSyncService(app_session, organization_id=user.organization_id)
        link = await service.import_order_payload(connector, payload)
        assert link.status == MarketplaceOrderLinkStatus.failed
        assert link.order_id is None

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")

        connector_a = await _setup_connector(app_session, user_a.organization_id, user_a.id)
        await _setup_product(app_session, user_a.organization_id, user_a.id)

        service_a = MarketplaceSyncService(app_session, organization_id=user_a.organization_id)
        service_b = MarketplaceSyncService(app_session, organization_id=user_b.organization_id)
        await service_a.sync_products(connector_a.id)

        links_b = await service_b.link_repo.list(connector_id=connector_a.id)
        assert links_b == []

    asyncio.run(_run())
