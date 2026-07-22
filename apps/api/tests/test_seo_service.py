import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.brand import BrandCreateRequest, BrandUpdateRequest
from app.schemas.category import CategoryCreateRequest, CategoryUpdateRequest
from app.services.auth_service import AuthService
from app.services.brand_service import BrandService
from app.services.category_service import CategoryService
from app.services.slug_redirect_service import SlugRedirectService


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


async def _register_org(session, email="owner@example.com", org_name="SEO Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


def test_brand_seo_fields_persisted(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = BrandService(app_session, organization_id=user.organization_id)
        brand = await service.create_brand(
            BrandCreateRequest(name="Acme", og_image_url="https://cdn.example.com/acme.png", canonical_url="https://example.com/acme", no_index=True),
            created_by=user.id,
        )
        assert brand.og_image_url == "https://cdn.example.com/acme.png"
        assert brand.no_index is True

    asyncio.run(_run())


def test_brand_rename_records_redirect(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = BrandService(app_session, organization_id=user.organization_id)
        brand = await service.create_brand(BrandCreateRequest(name="Acme Corp"), created_by=user.id)
        assert brand.slug == "acme-corp"

        await service.update_brand(brand.id, BrandUpdateRequest(name="Acme International"))

        seo_service = SlugRedirectService(app_session, organization_id=user.organization_id)
        resolved = await seo_service.resolve("brand", "acme-corp")
        assert resolved == "acme-international"

    asyncio.run(_run())


def test_category_rename_records_path_redirect(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CategoryService(app_session, organization_id=user.organization_id)
        category = await service.create_category(CategoryCreateRequest(name="Electronics"), created_by=user.id)
        assert category.path == "electronics"

        await service.update_category(category.id, CategoryUpdateRequest(name="Gadgets"))

        seo_service = SlugRedirectService(app_session, organization_id=user.organization_id)
        resolved = await seo_service.resolve("category", "electronics")
        assert resolved == "gadgets"

    asyncio.run(_run())


def test_redirect_chain_resolves_to_latest(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = BrandService(app_session, organization_id=user.organization_id)
        brand = await service.create_brand(BrandCreateRequest(name="Acme"), created_by=user.id)

        await service.update_brand(brand.id, BrandUpdateRequest(name="Acme Two"))
        await service.update_brand(brand.id, BrandUpdateRequest(name="Acme Three"))

        seo_service = SlugRedirectService(app_session, organization_id=user.organization_id)
        resolved = await seo_service.resolve("brand", "acme")
        assert resolved == "acme-three"

    asyncio.run(_run())


def test_no_redirect_when_slug_unchanged(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = BrandService(app_session, organization_id=user.organization_id)
        brand = await service.create_brand(BrandCreateRequest(name="Acme"), created_by=user.id)
        await service.update_brand(brand.id, BrandUpdateRequest(description="Updated description"))

        seo_service = SlugRedirectService(app_session, organization_id=user.organization_id)
        redirects = await seo_service.list_for_entity_type("brand")
        assert redirects == []

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")

        service_a = BrandService(app_session, organization_id=user_a.organization_id)
        brand = await service_a.create_brand(BrandCreateRequest(name="Acme"), created_by=user_a.id)
        await service_a.update_brand(brand.id, BrandUpdateRequest(name="Acme Renamed"))

        seo_service_b = SlugRedirectService(app_session, organization_id=user_b.organization_id)
        assert await seo_service_b.resolve("brand", "acme") is None

    asyncio.run(_run())
