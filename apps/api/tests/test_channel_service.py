import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.channel import ChannelCreateRequest
from app.schemas.product import ProductCreateRequest
from app.services.auth_service import AuthService
from app.services.channel_service import ChannelService
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


async def _register_org(session, email="owner@example.com", org_name="Channel Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


def test_create_channel_generates_code(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ChannelService(app_session, organization_id=user.organization_id)
        channel = await service.create_channel(ChannelCreateRequest(name="Online Store"), created_by=user.id)
        assert channel.code == "online-store"

    asyncio.run(_run())


def test_duplicate_code_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ChannelService(app_session, organization_id=user.organization_id)
        await service.create_channel(ChannelCreateRequest(name="Online Store"), created_by=user.id)
        with pytest.raises(HTTPException) as exc_info:
            await service.create_channel(ChannelCreateRequest(name="Online Store"), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_only_one_default_channel(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ChannelService(app_session, organization_id=user.organization_id)
        c1 = await service.create_channel(ChannelCreateRequest(name="Online Store", is_default=True), created_by=user.id)
        c2 = await service.create_channel(ChannelCreateRequest(name="POS", is_default=True), created_by=user.id)

        refreshed_c1 = await service.get_channel(c1.id)
        assert refreshed_c1.is_default is False
        assert c2.is_default is True

    asyncio.run(_run())


def test_assign_product_to_channels(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        channel_service = ChannelService(app_session, organization_id=user.organization_id)
        online = await channel_service.create_channel(ChannelCreateRequest(name="Online Store"), created_by=user.id)
        pos = await channel_service.create_channel(ChannelCreateRequest(name="POS"), created_by=user.id)

        product_service = ProductService(app_session, organization_id=user.organization_id)
        product = await product_service.create_product(ProductCreateRequest(name="Mouse", sku="M-1"), created_by=user.id)

        await channel_service.set_product_channels(product.id, [online.id, pos.id])
        assigned = await channel_service.get_product_channels(product.id)
        assert {a["channel_id"] for a in assigned} == {online.id, pos.id}
        assert all(a["is_published"] for a in assigned)

        await channel_service.set_product_channels(product.id, [online.id])
        assigned_after = await channel_service.get_product_channels(product.id)
        assert {a["channel_id"] for a in assigned_after} == {online.id}

    asyncio.run(_run())


def test_invalid_channel_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product_service = ProductService(app_session, organization_id=user.organization_id)
        product = await product_service.create_product(ProductCreateRequest(name="Mouse", sku="M-1"), created_by=user.id)

        channel_service = ChannelService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await channel_service.set_product_channels(product.id, ["does-not-exist"])
        assert exc_info.value.status_code == 404

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        service_a = ChannelService(app_session, organization_id=user_a.organization_id)
        service_b = ChannelService(app_session, organization_id=user_b.organization_id)

        channel = await service_a.create_channel(ChannelCreateRequest(name="Online Store"), created_by=user_a.id)
        assert await service_b.get_channel(channel.id) is None

    asyncio.run(_run())
