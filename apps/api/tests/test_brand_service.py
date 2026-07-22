import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.brand import BrandCreateRequest, BrandUpdateRequest
from app.services.auth_service import AuthService
from app.services.brand_service import BrandService


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


async def _register_org(session, email="owner@example.com", org_name="Brand Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


def test_create_brand_generates_slug(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = BrandService(app_session, organization_id=user.organization_id)
        brand = await service.create_brand(BrandCreateRequest(name="Acme Corp"), created_by=user.id)
        assert brand.slug == "acme-corp"
        assert brand.status.value == "active"

    asyncio.run(_run())


def test_duplicate_slug_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = BrandService(app_session, organization_id=user.organization_id)
        await service.create_brand(BrandCreateRequest(name="Acme Corp"), created_by=user.id)
        with pytest.raises(HTTPException) as exc_info:
            await service.create_brand(BrandCreateRequest(name="Acme Corp"), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_update_and_bulk_delete(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = BrandService(app_session, organization_id=user.organization_id)
        brand_a = await service.create_brand(BrandCreateRequest(name="Acme Corp"), created_by=user.id)
        brand_b = await service.create_brand(BrandCreateRequest(name="Globex"), created_by=user.id)

        updated = await service.update_brand(brand_a.id, BrandUpdateRequest(is_featured=True))
        assert updated.is_featured is True

        deleted_count = await service.bulk_delete([brand_a.id, brand_b.id])
        assert deleted_count == 2
        assert await service.get_brand(brand_a.id) is None
        assert await service.get_brand(brand_b.id) is None

    asyncio.run(_run())


def test_restore_brand(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = BrandService(app_session, organization_id=user.organization_id)
        brand = await service.create_brand(BrandCreateRequest(name="Acme Corp"), created_by=user.id)
        await service.delete_brand(brand.id)
        assert await service.get_brand(brand.id) is None
        restored = await service.restore_brand(brand.id)
        assert restored.id == brand.id

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        service_a = BrandService(app_session, organization_id=user_a.organization_id)
        service_b = BrandService(app_session, organization_id=user_b.organization_id)
        brand = await service_a.create_brand(BrandCreateRequest(name="Acme Corp"), created_by=user_a.id)
        assert await service_b.get_brand(brand.id) is None

    asyncio.run(_run())
