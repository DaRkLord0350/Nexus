import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.attribute import AttributeCreateRequest
from app.schemas.product import ProductCreateRequest
from app.schemas.product_type import ProductTypeAttributeConfig, ProductTypeCreateRequest
from app.services.attribute_service import AttributeService
from app.services.auth_service import AuthService
from app.services.product_service import ProductService
from app.services.product_type_service import ProductTypeService


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


async def _register_org(session, email="owner@example.com", org_name="Product Type Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


def test_create_product_type_generates_slug(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ProductTypeService(app_session, organization_id=user.organization_id)
        product_type = await service.create_product_type(ProductTypeCreateRequest(name="T-Shirt"), created_by=user.id)
        assert product_type.slug == "t-shirt"

    asyncio.run(_run())


def test_duplicate_slug_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ProductTypeService(app_session, organization_id=user.organization_id)
        await service.create_product_type(ProductTypeCreateRequest(name="T-Shirt"), created_by=user.id)
        with pytest.raises(HTTPException) as exc_info:
            await service.create_product_type(ProductTypeCreateRequest(name="T-Shirt"), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_set_and_get_attributes(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        attribute_service = AttributeService(app_session, organization_id=user.organization_id)
        color = await attribute_service.create_attribute(AttributeCreateRequest(name="Color"), created_by=user.id)
        size = await attribute_service.create_attribute(AttributeCreateRequest(name="Size"), created_by=user.id)

        service = ProductTypeService(app_session, organization_id=user.organization_id)
        product_type = await service.create_product_type(ProductTypeCreateRequest(name="T-Shirt"), created_by=user.id)

        await service.set_attributes(product_type.id, [
            ProductTypeAttributeConfig(attribute_id=color.id, is_required=True, sort_order=0),
            ProductTypeAttributeConfig(attribute_id=size.id, is_required=False, sort_order=1),
        ])

        attributes = await service.get_attributes(product_type.id)
        assert [a["name"] for a in attributes] == ["Color", "Size"]
        assert attributes[0]["is_required"] is True

    asyncio.run(_run())


def test_invalid_attribute_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ProductTypeService(app_session, organization_id=user.organization_id)
        product_type = await service.create_product_type(ProductTypeCreateRequest(name="T-Shirt"), created_by=user.id)
        with pytest.raises(HTTPException) as exc_info:
            await service.set_attributes(product_type.id, [ProductTypeAttributeConfig(attribute_id="does-not-exist")])
        assert exc_info.value.status_code == 404

    asyncio.run(_run())


def test_product_references_product_type(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        type_service = ProductTypeService(app_session, organization_id=user.organization_id)
        product_type = await type_service.create_product_type(ProductTypeCreateRequest(name="T-Shirt"), created_by=user.id)

        product_service = ProductService(app_session, organization_id=user.organization_id)
        product = await product_service.create_product(
            ProductCreateRequest(name="Basic Tee", sku="TEE-1", product_type_id=product_type.id), created_by=user.id,
        )
        assert product.product_type_id == product_type.id

        with pytest.raises(HTTPException) as exc_info:
            await product_service.create_product(
                ProductCreateRequest(name="Other Tee", sku="TEE-2", product_type_id="does-not-exist"), created_by=user.id,
            )
        assert exc_info.value.status_code == 404

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        service_a = ProductTypeService(app_session, organization_id=user_a.organization_id)
        service_b = ProductTypeService(app_session, organization_id=user_b.organization_id)

        product_type = await service_a.create_product_type(ProductTypeCreateRequest(name="T-Shirt"), created_by=user_a.id)
        assert await service_b.get_product_type(product_type.id) is None

    asyncio.run(_run())
