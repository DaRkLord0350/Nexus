import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.product import ProductCreateRequest
from app.schemas.reorder_rule import ReorderRuleCreateRequest, ReorderRuleUpdateRequest
from app.schemas.warehouse import WarehouseCreateRequest
from app.services.auth_service import AuthService
from app.services.product_service import ProductService
from app.services.reorder_rule_service import ReorderRuleService
from app.services.warehouse_service import WarehouseService


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


async def _register_org(session, email="owner@example.com", org_name="Reorder Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _setup(session, org_id, user_id):
    product_service = ProductService(session, organization_id=org_id)
    product = await product_service.create_product(ProductCreateRequest(name="Widget", sku="WID-1"), created_by=user_id)
    warehouse_service = WarehouseService(session, organization_id=org_id)
    warehouse = await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Main", code="MAIN"), created_by=user_id)
    return product, warehouse


def test_create_rule(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup(app_session, user.organization_id, user.id)
        service = ReorderRuleService(app_session, organization_id=user.organization_id)

        rule = await service.create_rule(ReorderRuleCreateRequest(
            product_id=product.id, warehouse_id=warehouse.id, minimum_stock=10, reorder_quantity=50, supplier_name="Acme",
        ))
        assert rule.minimum_stock == 10
        assert rule.reorder_quantity == 50
        assert rule.is_active is True

    asyncio.run(_run())


def test_duplicate_grain_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup(app_session, user.organization_id, user.id)
        service = ReorderRuleService(app_session, organization_id=user.organization_id)
        await service.create_rule(ReorderRuleCreateRequest(product_id=product.id, warehouse_id=warehouse.id, minimum_stock=10, reorder_quantity=50))
        with pytest.raises(HTTPException) as exc_info:
            await service.create_rule(ReorderRuleCreateRequest(product_id=product.id, warehouse_id=warehouse.id, minimum_stock=5, reorder_quantity=20))
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_update_and_delete_rule(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup(app_session, user.organization_id, user.id)
        service = ReorderRuleService(app_session, organization_id=user.organization_id)
        rule = await service.create_rule(ReorderRuleCreateRequest(product_id=product.id, warehouse_id=warehouse.id, minimum_stock=10, reorder_quantity=50))

        updated = await service.update_rule(rule.id, ReorderRuleUpdateRequest(is_active=False, reorder_quantity=75))
        assert updated.is_active is False
        assert updated.reorder_quantity == 75

        await service.delete_rule(rule.id)
        assert await service.get_rule(rule.id) is None

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        product_a, warehouse_a = await _setup(app_session, user_a.organization_id, user_a.id)

        service_a = ReorderRuleService(app_session, organization_id=user_a.organization_id)
        service_b = ReorderRuleService(app_session, organization_id=user_b.organization_id)
        rule = await service_a.create_rule(ReorderRuleCreateRequest(product_id=product_a.id, warehouse_id=warehouse_a.id, minimum_stock=10, reorder_quantity=50))

        assert await service_b.get_rule(rule.id) is None

    asyncio.run(_run())
