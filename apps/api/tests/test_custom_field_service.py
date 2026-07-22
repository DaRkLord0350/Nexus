import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.custom_field import CustomFieldDefinitionCreateRequest
from app.schemas.product import ProductCreateRequest
from app.services.auth_service import AuthService
from app.services.custom_field_service import CustomFieldService
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


async def _register_org(session, email="owner@example.com", org_name="Custom Field Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


def test_create_definition_generates_key(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CustomFieldService(app_session, organization_id=user.organization_id)
        definition = await service.create_definition(
            CustomFieldDefinitionCreateRequest(entity_type="product", name="Care Instructions"), created_by=user.id,
        )
        assert definition.key == "care_instructions"

    asyncio.run(_run())


def test_duplicate_key_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CustomFieldService(app_session, organization_id=user.organization_id)
        await service.create_definition(CustomFieldDefinitionCreateRequest(entity_type="product", name="Care Instructions"), created_by=user.id)
        with pytest.raises(HTTPException) as exc_info:
            await service.create_definition(CustomFieldDefinitionCreateRequest(entity_type="product", name="Care Instructions"), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_select_field_requires_options(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CustomFieldService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await service.create_definition(
                CustomFieldDefinitionCreateRequest(entity_type="product", name="Material", field_type="select"), created_by=user.id,
            )
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_set_and_get_values_for_product(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        field_service = CustomFieldService(app_session, organization_id=user.organization_id)
        await field_service.create_definition(
            CustomFieldDefinitionCreateRequest(entity_type="product", name="Care Instructions"), created_by=user.id,
        )
        await field_service.create_definition(
            CustomFieldDefinitionCreateRequest(entity_type="product", name="Warranty Months", field_type="number"), created_by=user.id,
        )

        product_service = ProductService(app_session, organization_id=user.organization_id)
        product = await product_service.create_product(ProductCreateRequest(name="Mouse", sku="M-1"), created_by=user.id)

        await field_service.set_values_for_entity("product", product.id, {"care_instructions": "Wipe clean", "warranty_months": 12})
        values = await field_service.get_values_for_entity("product", product.id)
        values_by_key = {v["key"]: v["value"] for v in values}
        assert values_by_key["care_instructions"] == "Wipe clean"
        assert values_by_key["warranty_months"] == 12

    asyncio.run(_run())


def test_invalid_number_value_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        field_service = CustomFieldService(app_session, organization_id=user.organization_id)
        await field_service.create_definition(
            CustomFieldDefinitionCreateRequest(entity_type="product", name="Warranty Months", field_type="number"), created_by=user.id,
        )
        with pytest.raises(HTTPException) as exc_info:
            await field_service.set_values_for_entity("product", "some-product-id", {"warranty_months": "not-a-number"})
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_unknown_key_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        field_service = CustomFieldService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await field_service.set_values_for_entity("product", "some-product-id", {"nonexistent_field": "value"})
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        service_a = CustomFieldService(app_session, organization_id=user_a.organization_id)
        service_b = CustomFieldService(app_session, organization_id=user_b.organization_id)

        await service_a.create_definition(CustomFieldDefinitionCreateRequest(entity_type="product", name="Care Instructions"), created_by=user_a.id)
        definitions_b, total_b = await service_b.list_definitions("product")
        assert total_b == 0

    asyncio.run(_run())
