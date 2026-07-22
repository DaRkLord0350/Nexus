import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.product import ProductCreateRequest, ProductUpdateRequest
from app.schemas.tag import TagCreateRequest
from app.services.auth_service import AuthService
from app.services.product_service import ProductService
from app.services.tag_service import TagService


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


async def _register_org(session, email="owner@example.com", org_name="Tag Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


def test_create_tag_generates_slug(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = TagService(app_session, organization_id=user.organization_id)
        tag = await service.create_tag(TagCreateRequest(name="Best Seller"))
        assert tag.slug == "best-seller"

    asyncio.run(_run())


def test_duplicate_tag_slug_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = TagService(app_session, organization_id=user.organization_id)
        await service.create_tag(TagCreateRequest(name="Best Seller"))
        with pytest.raises(HTTPException) as exc_info:
            await service.create_tag(TagCreateRequest(name="Best Seller"))
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_product_create_with_tag_names_reuses_existing_tags(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product_service = ProductService(app_session, organization_id=user.organization_id)

        product1 = await product_service.create_product(
            ProductCreateRequest(name="Mouse", sku="M-1", tag_names=["New", "Sale"]), created_by=user.id,
        )
        assert {t.name for t in product1.tags} == {"New", "Sale"}

        product2 = await product_service.create_product(
            ProductCreateRequest(name="Keyboard", sku="K-1", tag_names=["new", "Featured"]), created_by=user.id,
        )
        tag_names_2 = {t.name for t in product2.tags}
        assert "Featured" in tag_names_2

        tag_service = TagService(app_session, organization_id=user.organization_id)
        items, total = await tag_service.list_tags()
        assert total == 3

    asyncio.run(_run())


def test_update_product_replaces_tags(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product_service = ProductService(app_session, organization_id=user.organization_id)
        product = await product_service.create_product(
            ProductCreateRequest(name="Mouse", sku="M-1", tag_names=["New"]), created_by=user.id,
        )
        updated = await product_service.update_product(product.id, ProductUpdateRequest(tag_names=["Sale"]))
        assert [t.name for t in updated.tags] == ["Sale"]

    asyncio.run(_run())


def test_filter_products_by_tag(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product_service = ProductService(app_session, organization_id=user.organization_id)
        tagged = await product_service.create_product(
            ProductCreateRequest(name="Mouse", sku="M-1", tag_names=["Sale"]), created_by=user.id,
        )
        await product_service.create_product(ProductCreateRequest(name="Keyboard", sku="K-1"), created_by=user.id)

        tag_id = tagged.tags[0].id
        items, total = await product_service.list_products(tag_id=tag_id)
        assert total == 1
        assert items[0].id == tagged.id

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        service_a = TagService(app_session, organization_id=user_a.organization_id)
        service_b = TagService(app_session, organization_id=user_b.organization_id)

        tag = await service_a.create_tag(TagCreateRequest(name="Best Seller"))
        assert await service_b.get_tag(tag.id) is None

    asyncio.run(_run())
