import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.attribute import AttributeCreateRequest, AttributeValueCreateRequest
from app.schemas.product import ProductCreateRequest
from app.schemas.variant import VariantCreateRequest, VariantUpdateRequest
from app.services.attribute_service import AttributeService
from app.services.auth_service import AuthService
from app.services.product_service import ProductService
from app.services.variant_service import VariantService


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


async def _setup(session, email="owner@example.com", org_name="Variant Test Org"):
    auth_service = AuthService(session)
    user = await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )
    product_service = ProductService(session, organization_id=user.organization_id)
    product = await product_service.create_product(ProductCreateRequest(name="T-Shirt", sku="TSHIRT-001"), created_by=user.id)
    return user, product


def test_create_variant_marks_product_has_variants(app_session: AsyncSession):
    async def _run():
        user, product = await _setup(app_session)
        attribute_service = AttributeService(app_session, organization_id=user.organization_id)
        color = await attribute_service.create_attribute(AttributeCreateRequest(name="Color"), created_by=user.id)
        red = await attribute_service.create_value(color.id, AttributeValueCreateRequest(value="Red"))

        variant_service = VariantService(app_session, organization_id=user.organization_id)
        variant = await variant_service.create_variant(
            product.id, VariantCreateRequest(sku="TSHIRT-001-RED", attribute_value_ids=[red.id]), created_by=user.id,
        )
        assert variant.sku == "TSHIRT-001-RED"
        assert [v.id for v in variant.attribute_values] == [red.id]

        refreshed_product = await ProductService(app_session, organization_id=user.organization_id).get_product(product.id)
        assert refreshed_product.has_variants is True

    asyncio.run(_run())


def test_duplicate_variant_sku_rejected(app_session: AsyncSession):
    async def _run():
        user, product = await _setup(app_session)
        variant_service = VariantService(app_session, organization_id=user.organization_id)
        await variant_service.create_variant(product.id, VariantCreateRequest(sku="TSHIRT-001-RED"), created_by=user.id)
        with pytest.raises(HTTPException) as exc_info:
            await variant_service.create_variant(product.id, VariantCreateRequest(sku="TSHIRT-001-RED"), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_only_one_default_variant_per_product(app_session: AsyncSession):
    async def _run():
        user, product = await _setup(app_session)
        variant_service = VariantService(app_session, organization_id=user.organization_id)
        v1 = await variant_service.create_variant(product.id, VariantCreateRequest(sku="V1", is_default=True), created_by=user.id)
        v2 = await variant_service.create_variant(product.id, VariantCreateRequest(sku="V2", is_default=True), created_by=user.id)

        refreshed_v1 = await variant_service.get_variant(v1.id)
        assert refreshed_v1.is_default is False
        assert v2.is_default is True

        promoted = await variant_service.set_default_variant(v1.id)
        assert promoted.is_default is True
        refreshed_v2 = await variant_service.get_variant(v2.id)
        assert refreshed_v2.is_default is False

    asyncio.run(_run())


def test_update_variant_attribute_values(app_session: AsyncSession):
    async def _run():
        user, product = await _setup(app_session)
        attribute_service = AttributeService(app_session, organization_id=user.organization_id)
        size = await attribute_service.create_attribute(AttributeCreateRequest(name="Size"), created_by=user.id)
        small = await attribute_service.create_value(size.id, AttributeValueCreateRequest(value="Small"))
        large = await attribute_service.create_value(size.id, AttributeValueCreateRequest(value="Large"))

        variant_service = VariantService(app_session, organization_id=user.organization_id)
        variant = await variant_service.create_variant(product.id, VariantCreateRequest(sku="V1", attribute_value_ids=[small.id]), created_by=user.id)

        updated = await variant_service.update_variant(variant.id, VariantUpdateRequest(attribute_value_ids=[large.id]))
        assert [v.id for v in updated.attribute_values] == [large.id]

    asyncio.run(_run())


def test_invalid_attribute_value_rejected(app_session: AsyncSession):
    async def _run():
        user, product = await _setup(app_session)
        variant_service = VariantService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await variant_service.create_variant(product.id, VariantCreateRequest(sku="V1", attribute_value_ids=["nope"]), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_delete_variant(app_session: AsyncSession):
    async def _run():
        user, product = await _setup(app_session)
        variant_service = VariantService(app_session, organization_id=user.organization_id)
        variant = await variant_service.create_variant(product.id, VariantCreateRequest(sku="V1"), created_by=user.id)
        await variant_service.delete_variant(variant.id)
        assert await variant_service.get_variant(variant.id) is None

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a, product_a = await _setup(app_session, email="a@example.com", org_name="Org A")
        user_b, _ = await _setup(app_session, email="b@example.com", org_name="Org B")

        service_a = VariantService(app_session, organization_id=user_a.organization_id)
        service_b = VariantService(app_session, organization_id=user_b.organization_id)

        variant = await service_a.create_variant(product_a.id, VariantCreateRequest(sku="V1"), created_by=user_a.id)
        assert await service_b.get_variant(variant.id) is None

    asyncio.run(_run())
