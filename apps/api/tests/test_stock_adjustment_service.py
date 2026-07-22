import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.models.inventory_transaction import InventoryTransactionType
from app.schemas.product import ProductCreateRequest
from app.schemas.stock_adjustment import StockAdjustmentCreateRequest
from app.schemas.warehouse import WarehouseCreateRequest
from app.services.auth_service import AuthService
from app.services.inventory_service import InventoryService
from app.services.product_service import ProductService
from app.services.stock_adjustment_service import StockAdjustmentService
from app.services.stock_movement_service import StockMovementService
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


async def _register_org(session, email="owner@example.com", org_name="Adjustment Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _setup(session, org_id, user_id, initial_stock=50):
    product_service = ProductService(session, organization_id=org_id)
    product = await product_service.create_product(ProductCreateRequest(name="Widget", sku="WID-1"), created_by=user_id)
    warehouse_service = WarehouseService(session, organization_id=org_id)
    warehouse = await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Main", code="MAIN"), created_by=user_id)

    if initial_stock:
        movement_service = StockMovementService(session, organization_id=org_id)
        await movement_service.apply_movement(
            product_id=product.id, variant_id=None, warehouse_id=warehouse.id,
            transaction_type=InventoryTransactionType.receive, quantity_delta=initial_stock,
        )
    return product, warehouse


def test_positive_adjustment_increases_stock(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup(app_session, user.organization_id, user.id, initial_stock=0)
        service = StockAdjustmentService(app_session, organization_id=user.organization_id)

        adjustment = await service.create_adjustment(StockAdjustmentCreateRequest(
            product_id=product.id, warehouse_id=warehouse.id, quantity_delta=15, reason="found",
        ), created_by=user.id)
        assert adjustment.quantity_delta == 15
        assert adjustment.reason.value == "found"

        inventory_service = InventoryService(app_session, organization_id=user.organization_id)
        items, _ = await inventory_service.list_inventory(warehouse_id=warehouse.id)
        assert items[0].quantity_available == 15

    asyncio.run(_run())


def test_negative_adjustment_decreases_stock(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup(app_session, user.organization_id, user.id, initial_stock=50)
        service = StockAdjustmentService(app_session, organization_id=user.organization_id)

        await service.create_adjustment(StockAdjustmentCreateRequest(
            product_id=product.id, warehouse_id=warehouse.id, quantity_delta=-10, reason="damage",
        ), created_by=user.id)

        inventory_service = InventoryService(app_session, organization_id=user.organization_id)
        items, _ = await inventory_service.list_inventory(warehouse_id=warehouse.id)
        assert items[0].quantity_available == 40

    asyncio.run(_run())


def test_negative_adjustment_below_zero_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup(app_session, user.organization_id, user.id, initial_stock=5)
        service = StockAdjustmentService(app_session, organization_id=user.organization_id)

        with pytest.raises(HTTPException) as exc_info:
            await service.create_adjustment(StockAdjustmentCreateRequest(
                product_id=product.id, warehouse_id=warehouse.id, quantity_delta=-10, reason="lost",
            ), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_zero_delta_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup(app_session, user.organization_id, user.id)
        service = StockAdjustmentService(app_session, organization_id=user.organization_id)

        with pytest.raises(HTTPException) as exc_info:
            await service.create_adjustment(StockAdjustmentCreateRequest(
                product_id=product.id, warehouse_id=warehouse.id, quantity_delta=0,
            ), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_list_adjustments_filters_by_reason(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup(app_session, user.organization_id, user.id, initial_stock=100)
        service = StockAdjustmentService(app_session, organization_id=user.organization_id)
        await service.create_adjustment(StockAdjustmentCreateRequest(product_id=product.id, warehouse_id=warehouse.id, quantity_delta=-5, reason="damage"), created_by=user.id)
        await service.create_adjustment(StockAdjustmentCreateRequest(product_id=product.id, warehouse_id=warehouse.id, quantity_delta=5, reason="found"), created_by=user.id)

        damage_items, damage_total = await service.list_adjustments(reason="damage")
        assert damage_total == 1
        assert damage_items[0].reason.value == "damage"

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        product_a, warehouse_a = await _setup(app_session, user_a.organization_id, user_a.id, initial_stock=50)

        service_a = StockAdjustmentService(app_session, organization_id=user_a.organization_id)
        service_b = StockAdjustmentService(app_session, organization_id=user_b.organization_id)
        adjustment = await service_a.create_adjustment(StockAdjustmentCreateRequest(
            product_id=product_a.id, warehouse_id=warehouse_a.id, quantity_delta=-5, reason="damage",
        ), created_by=user_a.id)

        assert await service_b.get_adjustment(adjustment.id) is None

    asyncio.run(_run())
