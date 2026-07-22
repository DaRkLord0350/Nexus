import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.collection import CollectionCreateRequest, CollectionRuleCondition
from app.schemas.product import ProductCreateRequest
from app.services.auth_service import AuthService
from app.services.collection_service import CollectionService
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


async def _register_org(session, email="owner@example.com", org_name="Collection Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


def test_create_manual_collection_and_add_products(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product_service = ProductService(app_session, organization_id=user.organization_id)
        p1 = await product_service.create_product(ProductCreateRequest(name="Mouse", sku="M-1"), created_by=user.id)
        p2 = await product_service.create_product(ProductCreateRequest(name="Keyboard", sku="K-1"), created_by=user.id)

        service = CollectionService(app_session, organization_id=user.organization_id)
        collection = await service.create_collection(CollectionCreateRequest(name="Best Sellers"), created_by=user.id)
        assert collection.slug == "best-sellers"

        await service.add_products(collection.id, [p1.id, p2.id])
        products = await service.get_products(collection.id)
        assert {p.id for p in products} == {p1.id, p2.id}

        notifications = await service.notification_service.list_notifications(user.id)
        assert any("collection" in n.title.lower() for n in notifications)

    asyncio.run(_run())


def test_dynamic_collection_resolves_by_rule(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product_service = ProductService(app_session, organization_id=user.organization_id)
        featured = await product_service.create_product(ProductCreateRequest(name="Featured Mouse", sku="M-1", is_featured=True), created_by=user.id)
        await product_service.create_product(ProductCreateRequest(name="Regular Keyboard", sku="K-1", is_featured=False), created_by=user.id)

        service = CollectionService(app_session, organization_id=user.organization_id)
        collection = await service.create_collection(
            CollectionCreateRequest(
                name="Featured Items",
                collection_type="dynamic",
                rules=[CollectionRuleCondition(field="is_featured", operator="eq", value=True)],
            ),
            created_by=user.id,
        )

        products = await service.get_products(collection.id)
        assert [p.id for p in products] == [featured.id]

    asyncio.run(_run())


def test_cannot_manually_add_products_to_dynamic_collection(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product_service = ProductService(app_session, organization_id=user.organization_id)
        product = await product_service.create_product(ProductCreateRequest(name="Mouse", sku="M-1"), created_by=user.id)

        service = CollectionService(app_session, organization_id=user.organization_id)
        collection = await service.create_collection(CollectionCreateRequest(name="Dynamic", collection_type="dynamic"), created_by=user.id)

        with pytest.raises(HTTPException) as exc_info:
            await service.add_products(collection.id, [product.id])
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_duplicate_slug_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CollectionService(app_session, organization_id=user.organization_id)
        await service.create_collection(CollectionCreateRequest(name="Best Sellers"), created_by=user.id)
        with pytest.raises(HTTPException) as exc_info:
            await service.create_collection(CollectionCreateRequest(name="Best Sellers"), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_delete_and_restore_collection(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CollectionService(app_session, organization_id=user.organization_id)
        collection = await service.create_collection(CollectionCreateRequest(name="Seasonal"), created_by=user.id)
        await service.delete_collection(collection.id)
        assert await service.get_collection(collection.id) is None
        restored = await service.restore_collection(collection.id)
        assert restored.id == collection.id

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        service_a = CollectionService(app_session, organization_id=user_a.organization_id)
        service_b = CollectionService(app_session, organization_id=user_b.organization_id)

        collection = await service_a.create_collection(CollectionCreateRequest(name="Best Sellers"), created_by=user_a.id)
        assert await service_b.get_collection(collection.id) is None

    asyncio.run(_run())
