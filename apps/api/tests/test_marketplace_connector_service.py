import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.marketplace_connector import MarketplaceConnectorCreateRequest, MarketplaceConnectorUpdateRequest
from app.services.auth_service import AuthService
from app.services.marketplace_connector_service import MarketplaceConnectorService


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


async def _register_org(session, email="owner@example.com", org_name="Marketplace Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


def test_create_connector_with_credentials(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = MarketplaceConnectorService(app_session, organization_id=user.organization_id)

        connector = await service.create_connector(MarketplaceConnectorCreateRequest(
            name="My WooCommerce Store", code="woo-main", connector_type="woocommerce",
            credentials={"consumer_key": "ck_123", "consumer_secret": "cs_456"},
            store_url="https://shop.example.com",
        ), created_by=user.id)

        assert connector.code == "woo-main"
        assert connector.connector_type == "woocommerce"
        assert connector.credentials == '{"consumer_key": "ck_123", "consumer_secret": "cs_456"}'

    asyncio.run(_run())


def test_duplicate_code_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = MarketplaceConnectorService(app_session, organization_id=user.organization_id)
        await service.create_connector(MarketplaceConnectorCreateRequest(name="A", code="dup"), created_by=user.id)

        with pytest.raises(HTTPException) as exc_info:
            await service.create_connector(MarketplaceConnectorCreateRequest(name="B", code="dup"), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_update_connector(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = MarketplaceConnectorService(app_session, organization_id=user.organization_id)
        connector = await service.create_connector(MarketplaceConnectorCreateRequest(name="A", code="a"), created_by=user.id)

        updated = await service.update_connector(connector.id, MarketplaceConnectorUpdateRequest(is_active=False, auto_sync_orders=True))
        assert updated.is_active is False
        assert updated.auto_sync_orders is True

    asyncio.run(_run())


def test_delete_connector(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = MarketplaceConnectorService(app_session, organization_id=user.organization_id)
        connector = await service.create_connector(MarketplaceConnectorCreateRequest(name="A", code="a"), created_by=user.id)

        await service.delete_connector(connector.id)
        assert await service.get_connector(connector.id) is None

    asyncio.run(_run())


def test_list_connectors_filters_by_type(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = MarketplaceConnectorService(app_session, organization_id=user.organization_id)
        await service.create_connector(MarketplaceConnectorCreateRequest(name="Woo", code="woo", connector_type="woocommerce"), created_by=user.id)
        await service.create_connector(MarketplaceConnectorCreateRequest(name="Amz", code="amz", connector_type="amazon"), created_by=user.id)

        items, total = await service.list_connectors(connector_type="amazon")
        assert total == 1
        assert items[0].code == "amz"

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")

        service_a = MarketplaceConnectorService(app_session, organization_id=user_a.organization_id)
        service_b = MarketplaceConnectorService(app_session, organization_id=user_b.organization_id)
        connector = await service_a.create_connector(MarketplaceConnectorCreateRequest(name="A", code="a"), created_by=user_a.id)

        assert await service_b.get_connector(connector.id) is None

    asyncio.run(_run())
