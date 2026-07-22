import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.attribute import (
    AttributeCreateRequest,
    AttributeUpdateRequest,
    AttributeValueCreateRequest,
    AttributeValueUpdateRequest,
)
from app.services.attribute_service import AttributeService
from app.services.auth_service import AuthService


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


async def _register_org(session, email="owner@example.com", org_name="Attribute Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


def test_create_attribute_and_values(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = AttributeService(app_session, organization_id=user.organization_id)

        attribute = await service.create_attribute(AttributeCreateRequest(name="Color"), created_by=user.id)
        assert attribute.code == "color"

        red = await service.create_value(attribute.id, AttributeValueCreateRequest(value="Red", color_hex="#FF0000"))
        blue = await service.create_value(attribute.id, AttributeValueCreateRequest(value="Blue"))
        assert red.slug == "red"

        values = await service.list_values(attribute.id)
        assert {v.id for v in values} == {red.id, blue.id}

    asyncio.run(_run())


def test_duplicate_code_and_value_slug_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = AttributeService(app_session, organization_id=user.organization_id)
        attribute = await service.create_attribute(AttributeCreateRequest(name="Color"), created_by=user.id)

        with pytest.raises(HTTPException) as exc_info:
            await service.create_attribute(AttributeCreateRequest(name="Color"), created_by=user.id)
        assert exc_info.value.status_code == 400

        await service.create_value(attribute.id, AttributeValueCreateRequest(value="Red"))
        with pytest.raises(HTTPException) as exc_info:
            await service.create_value(attribute.id, AttributeValueCreateRequest(value="Red"))
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_update_value(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = AttributeService(app_session, organization_id=user.organization_id)
        attribute = await service.create_attribute(AttributeCreateRequest(name="Size"), created_by=user.id)
        value = await service.create_value(attribute.id, AttributeValueCreateRequest(value="Small"))

        updated = await service.update_value(attribute.id, value.id, AttributeValueUpdateRequest(sort_order=5))
        assert updated.sort_order == 5

    asyncio.run(_run())


def test_delete_attribute_cascades_to_values(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = AttributeService(app_session, organization_id=user.organization_id)
        attribute = await service.create_attribute(AttributeCreateRequest(name="Size"), created_by=user.id)
        value = await service.create_value(attribute.id, AttributeValueCreateRequest(value="Small"))

        await service.delete_attribute(attribute.id)
        assert await service.get_attribute(attribute.id) is None

        remaining_values = await service.value_repo.list_for_attribute(attribute.id)
        assert remaining_values == []
        assert await service.value_repo.get_by_id(value.id) is None

    asyncio.run(_run())


def test_attribute_update_rejects_invalid_target(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = AttributeService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await service.update_attribute("does-not-exist", AttributeUpdateRequest(name="X"))
        assert exc_info.value.status_code == 404

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        service_a = AttributeService(app_session, organization_id=user_a.organization_id)
        service_b = AttributeService(app_session, organization_id=user_b.organization_id)

        attribute = await service_a.create_attribute(AttributeCreateRequest(name="Color"), created_by=user_a.id)
        assert await service_b.get_attribute(attribute.id) is None

    asyncio.run(_run())
