import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.models.product import ProductStatus
from app.schemas.product import ProductCreateRequest, ProductUpdateRequest
from app.services.auth_service import AuthService
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


async def _register_org(session, email="owner@example.com", org_name="Product Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


def test_create_product_generates_slug(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ProductService(app_session, organization_id=user.organization_id)
        product = await service.create_product(ProductCreateRequest(name="Wireless Mouse", sku="WM-001"), created_by=user.id)
        assert product.slug == "wireless-mouse"
        assert product.status.value == "draft"
        assert product.published_at is None

    asyncio.run(_run())


def test_duplicate_slug_and_sku_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ProductService(app_session, organization_id=user.organization_id)
        await service.create_product(ProductCreateRequest(name="Wireless Mouse", sku="WM-001"), created_by=user.id)

        with pytest.raises(HTTPException) as exc_info:
            await service.create_product(ProductCreateRequest(name="Wireless Mouse", sku="WM-002"), created_by=user.id)
        assert exc_info.value.status_code == 400

        with pytest.raises(HTTPException) as exc_info:
            await service.create_product(ProductCreateRequest(name="Other Mouse", sku="WM-001"), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_publish_sets_published_at_and_notifies(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ProductService(app_session, organization_id=user.organization_id)
        product = await service.create_product(ProductCreateRequest(name="Wireless Mouse", sku="WM-001"), created_by=user.id)

        published = await service.publish_product(product.id, user.id)
        assert published.status == ProductStatus.published
        assert published.published_at is not None

        notifications = await service.notification_service.list_notifications(user.id)
        assert any("published" in n.title.lower() for n in notifications)

    asyncio.run(_run())


def test_invalid_brand_reference_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ProductService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await service.create_product(ProductCreateRequest(name="Wireless Mouse", sku="WM-001", brand_id="does-not-exist"), created_by=user.id)
        assert exc_info.value.status_code == 404

    asyncio.run(_run())


def test_bulk_status_update(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ProductService(app_session, organization_id=user.organization_id)
        p1 = await service.create_product(ProductCreateRequest(name="Mouse", sku="M-1"), created_by=user.id)
        p2 = await service.create_product(ProductCreateRequest(name="Keyboard", sku="K-1"), created_by=user.id)

        updated = await service.bulk_update_status([p1.id, p2.id], ProductStatus.archived)
        assert updated == 2
        refreshed = await service.get_product(p1.id)
        assert refreshed.status == ProductStatus.archived

    asyncio.run(_run())


def test_delete_and_restore(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ProductService(app_session, organization_id=user.organization_id)
        product = await service.create_product(ProductCreateRequest(name="Mouse", sku="M-1"), created_by=user.id)

        await service.delete_product(product.id)
        assert await service.get_product(product.id) is None

        restored = await service.restore_product(product.id)
        assert restored.id == product.id

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        service_a = ProductService(app_session, organization_id=user_a.organization_id)
        service_b = ProductService(app_session, organization_id=user_b.organization_id)

        product = await service_a.create_product(ProductCreateRequest(name="Mouse", sku="M-1"), created_by=user_a.id)
        assert await service_b.get_product(product.id) is None
        # SKU uniqueness must not leak across tenants either.
        other = await service_b.create_product(ProductCreateRequest(name="Mouse", sku="M-1"), created_by=user_b.id)
        assert other.id != product.id

    asyncio.run(_run())
