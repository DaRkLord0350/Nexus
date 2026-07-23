import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.shipping_provider import ShippingProviderCreateRequest, ShippingProviderUpdateRequest
from app.services.auth_service import AuthService
from app.services.shipping_provider_service import ShippingProviderService


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


async def _register_org(session, email="owner@example.com", org_name="Shipping Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


def test_create_provider_with_credentials(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ShippingProviderService(app_session, organization_id=user.organization_id)

        provider = await service.create_provider(ShippingProviderCreateRequest(
            name="Shiprocket Main", code="shiprocket-main", provider_type="shiprocket",
            credentials={"api_key": "abc123"}, is_default=True,
        ), created_by=user.id)

        assert provider.code == "shiprocket-main"
        assert provider.is_default is True
        assert provider.credentials == '{"api_key": "abc123"}'

    asyncio.run(_run())


def test_duplicate_code_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ShippingProviderService(app_session, organization_id=user.organization_id)
        await service.create_provider(ShippingProviderCreateRequest(name="A", code="dup"), created_by=user.id)

        with pytest.raises(HTTPException) as exc_info:
            await service.create_provider(ShippingProviderCreateRequest(name="B", code="dup"), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_only_one_default_provider(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ShippingProviderService(app_session, organization_id=user.organization_id)

        first = await service.create_provider(ShippingProviderCreateRequest(name="A", code="a", is_default=True), created_by=user.id)
        second = await service.create_provider(ShippingProviderCreateRequest(name="B", code="b", is_default=True), created_by=user.id)

        default = await service.get_default_provider()
        assert default.id == second.id

        # unset_default is a bulk UPDATE that bypasses the ORM identity map;
        # this long-lived test session already holds `first` in memory, so an
        # explicit refresh is needed to observe it (a fresh per-request
        # session, as FastAPI uses in production, wouldn't have this staleness).
        await app_session.refresh(first)
        assert first.is_default is False

    asyncio.run(_run())


def test_update_provider_default_switch(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ShippingProviderService(app_session, organization_id=user.organization_id)

        first = await service.create_provider(ShippingProviderCreateRequest(name="A", code="a", is_default=True), created_by=user.id)
        second = await service.create_provider(ShippingProviderCreateRequest(name="B", code="b"), created_by=user.id)

        await service.update_provider(second.id, ShippingProviderUpdateRequest(is_default=True))

        await app_session.refresh(first)
        refreshed_second = await service.get_provider(second.id)
        assert first.is_default is False
        assert refreshed_second.is_default is True

    asyncio.run(_run())


def test_delete_provider(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ShippingProviderService(app_session, organization_id=user.organization_id)
        provider = await service.create_provider(ShippingProviderCreateRequest(name="A", code="a"), created_by=user.id)

        await service.delete_provider(provider.id)
        assert await service.get_provider(provider.id) is None

    asyncio.run(_run())


def test_list_providers_sorted_by_priority(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ShippingProviderService(app_session, organization_id=user.organization_id)
        await service.create_provider(ShippingProviderCreateRequest(name="Low priority", code="low", priority=10), created_by=user.id)
        await service.create_provider(ShippingProviderCreateRequest(name="High priority", code="high", priority=1), created_by=user.id)

        items, total = await service.list_providers()
        assert total == 2
        assert items[0].code == "high"

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")

        service_a = ShippingProviderService(app_session, organization_id=user_a.organization_id)
        service_b = ShippingProviderService(app_session, organization_id=user_b.organization_id)
        provider = await service_a.create_provider(ShippingProviderCreateRequest(name="A", code="a"), created_by=user_a.id)

        assert await service_b.get_provider(provider.id) is None

    asyncio.run(_run())

