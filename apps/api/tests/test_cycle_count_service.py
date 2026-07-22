import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.models.inventory_transaction import InventoryTransactionType
from app.schemas.cycle_count import CycleCountCreateRequest, CycleCountItemInput, CycleCountRecordRequest
from app.schemas.product import ProductCreateRequest
from app.schemas.warehouse import WarehouseCreateRequest
from app.services.auth_service import AuthService
from app.services.cycle_count_service import CycleCountService
from app.services.inventory_service import InventoryService
from app.services.product_service import ProductService
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


async def _register_org(session, email="owner@example.com", org_name="CycleCount Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _setup(session, org_id, user_id, initial_stock=50):
    product_service = ProductService(session, organization_id=org_id)
    product = await product_service.create_product(ProductCreateRequest(name="Widget", sku="WID-1"), created_by=user_id)
    warehouse_service = WarehouseService(session, organization_id=org_id)
    warehouse = await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Main", code="MAIN"), created_by=user_id)

    movement_service = StockMovementService(session, organization_id=org_id)
    await movement_service.apply_movement(
        product_id=product.id, variant_id=None, warehouse_id=warehouse.id,
        transaction_type=InventoryTransactionType.receive, quantity_delta=initial_stock,
    )
    return product, warehouse


def test_create_cycle_count_seeds_expected_quantity(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup(app_session, user.organization_id, user.id, initial_stock=60)
        service = CycleCountService(app_session, organization_id=user.organization_id)

        cycle_count = await service.create_cycle_count(CycleCountCreateRequest(
            warehouse_id=warehouse.id, items=[CycleCountItemInput(product_id=product.id)],
        ))
        items = await service.get_items(cycle_count.id)
        assert len(items) == 1
        assert items[0].expected_quantity == 60
        assert items[0].actual_quantity is None

    asyncio.run(_run())


def test_record_count_computes_variance_and_moves_to_in_progress(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup(app_session, user.organization_id, user.id, initial_stock=60)
        service = CycleCountService(app_session, organization_id=user.organization_id)
        cycle_count = await service.create_cycle_count(CycleCountCreateRequest(
            warehouse_id=warehouse.id, items=[CycleCountItemInput(product_id=product.id)],
        ))
        items = await service.get_items(cycle_count.id)

        recorded = await service.record_count(cycle_count.id, items[0].id, CycleCountRecordRequest(actual_quantity=55), counted_by=user.id)
        assert recorded.actual_quantity == 55
        assert recorded.variance == -5

        refreshed = await service.get_cycle_count(cycle_count.id)
        assert refreshed.status.value == "in_progress"
        assert refreshed.started_at is not None

    asyncio.run(_run())


def test_complete_count_applies_variance_to_inventory(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup(app_session, user.organization_id, user.id, initial_stock=60)
        service = CycleCountService(app_session, organization_id=user.organization_id)
        cycle_count = await service.create_cycle_count(CycleCountCreateRequest(
            warehouse_id=warehouse.id, items=[CycleCountItemInput(product_id=product.id)],
        ))
        items = await service.get_items(cycle_count.id)
        await service.record_count(cycle_count.id, items[0].id, CycleCountRecordRequest(actual_quantity=55), counted_by=user.id)

        completed = await service.complete_count(cycle_count.id, user_id=user.id)
        assert completed.status.value == "completed"
        assert completed.completed_at is not None

        inventory_service = InventoryService(app_session, organization_id=user.organization_id)
        inventory_items, _ = await inventory_service.list_inventory(warehouse_id=warehouse.id)
        assert inventory_items[0].quantity_available == 55

    asyncio.run(_run())


def test_cannot_complete_with_uncounted_items(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup(app_session, user.organization_id, user.id, initial_stock=60)
        service = CycleCountService(app_session, organization_id=user.organization_id)
        cycle_count = await service.create_cycle_count(CycleCountCreateRequest(
            warehouse_id=warehouse.id, items=[CycleCountItemInput(product_id=product.id)],
        ))

        with pytest.raises(HTTPException) as exc_info:
            await service.complete_count(cycle_count.id, user_id=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_cancel_cycle_count(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup(app_session, user.organization_id, user.id)
        service = CycleCountService(app_session, organization_id=user.organization_id)
        cycle_count = await service.create_cycle_count(CycleCountCreateRequest(warehouse_id=warehouse.id))

        cancelled = await service.cancel_cycle_count(cycle_count.id)
        assert cancelled.status.value == "cancelled"

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        product_a, warehouse_a = await _setup(app_session, user_a.organization_id, user_a.id)

        service_a = CycleCountService(app_session, organization_id=user_a.organization_id)
        service_b = CycleCountService(app_session, organization_id=user_b.organization_id)
        cycle_count = await service_a.create_cycle_count(CycleCountCreateRequest(warehouse_id=warehouse_a.id))

        assert await service_b.get_cycle_count(cycle_count.id) is None

    asyncio.run(_run())
