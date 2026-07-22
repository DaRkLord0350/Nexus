import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.models.inventory_transaction import InventoryTransactionType
from app.schemas.product import ProductCreateRequest
from app.schemas.stock_transfer import StockTransferCreateRequest, StockTransferLineItemInput
from app.schemas.warehouse import WarehouseCreateRequest
from app.services.auth_service import AuthService
from app.services.inventory_service import InventoryService
from app.services.product_service import ProductService
from app.services.stock_movement_service import StockMovementService
from app.services.transfer_service import TransferService
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


async def _register_org(session, email="owner@example.com", org_name="Transfer Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _setup(session, org_id, user_id):
    product_service = ProductService(session, organization_id=org_id)
    product = await product_service.create_product(ProductCreateRequest(name="Widget", sku="WID-1"), created_by=user_id)
    warehouse_service = WarehouseService(session, organization_id=org_id)
    warehouse_a = await warehouse_service.create_warehouse(WarehouseCreateRequest(name="A", code="A"), created_by=user_id)
    warehouse_b = await warehouse_service.create_warehouse(WarehouseCreateRequest(name="B", code="B"), created_by=user_id)

    movement_service = StockMovementService(session, organization_id=org_id)
    await movement_service.apply_movement(
        product_id=product.id, variant_id=None, warehouse_id=warehouse_a.id,
        transaction_type=InventoryTransactionType.receive, quantity_delta=100,
    )
    return product, warehouse_a, warehouse_b


def test_from_and_to_warehouse_must_differ(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse_a, warehouse_b = await _setup(app_session, user.organization_id, user.id)
        service = TransferService(app_session, organization_id=user.organization_id)

        with pytest.raises(HTTPException) as exc_info:
            await service.create_transfer(StockTransferCreateRequest(from_warehouse_id=warehouse_a.id, to_warehouse_id=warehouse_a.id), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_full_transfer_workflow_moves_stock(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse_a, warehouse_b = await _setup(app_session, user.organization_id, user.id)
        service = TransferService(app_session, organization_id=user.organization_id)

        transfer = await service.create_transfer(StockTransferCreateRequest(
            from_warehouse_id=warehouse_a.id, to_warehouse_id=warehouse_b.id,
            items=[StockTransferLineItemInput(product_id=product.id, quantity_requested=30)],
        ), created_by=user.id)

        packed = await service.pack_transfer(transfer.id)
        assert packed.status.value == "packed"

        shipped = await service.ship_transfer(transfer.id, user_id=user.id)
        assert shipped.status.value == "shipped"
        assert shipped.shipped_at is not None

        inventory_service = InventoryService(app_session, organization_id=user.organization_id)
        items_a, _ = await inventory_service.list_inventory(warehouse_id=warehouse_a.id)
        assert items_a[0].quantity_available == 70

        received = await service.receive_transfer(transfer.id, user_id=user.id)
        assert received.status.value == "received"
        assert received.received_at is not None

        items_b, _ = await inventory_service.list_inventory(warehouse_id=warehouse_b.id)
        assert items_b[0].quantity_available == 30

        items_a_after, _ = await inventory_service.list_inventory(warehouse_id=warehouse_a.id)
        assert items_a_after[0].quantity_available == 70

    asyncio.run(_run())


def test_cannot_ship_unpacked_transfer(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse_a, warehouse_b = await _setup(app_session, user.organization_id, user.id)
        service = TransferService(app_session, organization_id=user.organization_id)
        transfer = await service.create_transfer(StockTransferCreateRequest(
            from_warehouse_id=warehouse_a.id, to_warehouse_id=warehouse_b.id,
            items=[StockTransferLineItemInput(product_id=product.id, quantity_requested=10)],
        ), created_by=user.id)

        with pytest.raises(HTTPException) as exc_info:
            await service.ship_transfer(transfer.id, user_id=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_ship_rejects_insufficient_stock(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse_a, warehouse_b = await _setup(app_session, user.organization_id, user.id)
        service = TransferService(app_session, organization_id=user.organization_id)
        transfer = await service.create_transfer(StockTransferCreateRequest(
            from_warehouse_id=warehouse_a.id, to_warehouse_id=warehouse_b.id,
            items=[StockTransferLineItemInput(product_id=product.id, quantity_requested=999)],
        ), created_by=user.id)
        await service.pack_transfer(transfer.id)

        with pytest.raises(HTTPException) as exc_info:
            await service.ship_transfer(transfer.id, user_id=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_cancel_transfer(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse_a, warehouse_b = await _setup(app_session, user.organization_id, user.id)
        service = TransferService(app_session, organization_id=user.organization_id)
        transfer = await service.create_transfer(StockTransferCreateRequest(
            from_warehouse_id=warehouse_a.id, to_warehouse_id=warehouse_b.id,
            items=[StockTransferLineItemInput(product_id=product.id, quantity_requested=10)],
        ), created_by=user.id)

        cancelled = await service.cancel_transfer(transfer.id)
        assert cancelled.status.value == "cancelled"

        with pytest.raises(HTTPException) as exc_info:
            await service.pack_transfer(transfer.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        product_a, wh_a1, wh_a2 = await _setup(app_session, user_a.organization_id, user_a.id)

        service_a = TransferService(app_session, organization_id=user_a.organization_id)
        service_b = TransferService(app_session, organization_id=user_b.organization_id)
        transfer = await service_a.create_transfer(StockTransferCreateRequest(
            from_warehouse_id=wh_a1.id, to_warehouse_id=wh_a2.id,
            items=[StockTransferLineItemInput(product_id=product_a.id, quantity_requested=5)],
        ), created_by=user_a.id)

        assert await service_b.get_transfer(transfer.id) is None

    asyncio.run(_run())
