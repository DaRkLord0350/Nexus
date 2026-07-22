import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.goods_receipt import GoodsReceiptCreateRequest, GoodsReceiptItemInput
from app.schemas.product import ProductCreateRequest
from app.schemas.purchase_order import PurchaseOrderCreateRequest, PurchaseOrderLineItemInput
from app.schemas.warehouse import WarehouseCreateRequest
from app.services.auth_service import AuthService
from app.services.goods_receipt_service import GoodsReceiptService
from app.services.inventory_service import InventoryService
from app.services.product_service import ProductService
from app.services.purchase_order_service import PurchaseOrderService
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


async def _register_org(session, email="owner@example.com", org_name="GR Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _setup_product_and_warehouse(session, org_id, user_id):
    product_service = ProductService(session, organization_id=org_id)
    product = await product_service.create_product(ProductCreateRequest(name="Widget", sku="WID-1"), created_by=user_id)
    warehouse_service = WarehouseService(session, organization_id=org_id)
    warehouse = await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Main", code="MAIN"), created_by=user_id)
    return product, warehouse


def test_complete_receipt_without_po_updates_inventory(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = GoodsReceiptService(app_session, organization_id=user.organization_id)

        receipt = await service.create_goods_receipt(GoodsReceiptCreateRequest(
            warehouse_id=warehouse.id,
            items=[GoodsReceiptItemInput(product_id=product.id, quantity_received=40, unit_cost=2.0)],
        ))
        completed = await service.complete_receipt(receipt.id, user_id=user.id)
        assert completed.status.value == "completed"
        assert completed.receiver_id == user.id

        inventory_service = InventoryService(app_session, organization_id=user.organization_id)
        items, total = await inventory_service.list_inventory(warehouse_id=warehouse.id)
        assert total == 1
        assert items[0].quantity_available == 40

        transactions, txn_total = await inventory_service.list_transactions(warehouse_id=warehouse.id)
        assert txn_total == 1
        assert transactions[0].type.value == "receive"
        assert transactions[0].reference_type == "goods_receipt"
        assert transactions[0].reference_id == receipt.id

    asyncio.run(_run())


def test_complete_receipt_creates_batch(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = GoodsReceiptService(app_session, organization_id=user.organization_id)

        receipt = await service.create_goods_receipt(GoodsReceiptCreateRequest(
            warehouse_id=warehouse.id,
            items=[GoodsReceiptItemInput(product_id=product.id, quantity_received=25, batch_number="LOT-100", unit_cost=1.5)],
        ))
        await service.complete_receipt(receipt.id, user_id=user.id)

        from app.services.batch_service import BatchService
        batch_service = BatchService(app_session, organization_id=user.organization_id)
        batches, batch_total = await batch_service.list_batches(product_id=product.id, warehouse_id=warehouse.id)
        assert batch_total == 1
        assert batches[0].batch_number == "LOT-100"
        assert batches[0].remaining_quantity == 25

    asyncio.run(_run())


def test_complete_receipt_updates_purchase_order_status(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        po_service = PurchaseOrderService(app_session, organization_id=user.organization_id)
        po = await po_service.create_purchase_order(PurchaseOrderCreateRequest(
            supplier_name="Acme", warehouse_id=warehouse.id,
            items=[PurchaseOrderLineItemInput(product_id=product.id, quantity_ordered=20, unit_cost=1.0)],
        ), created_by=user.id)
        po_items = await po_service.item_repo.list_for_order(po.id)
        po_item = po_items[0]
        await po_service.send_purchase_order(po.id)

        receipt_service = GoodsReceiptService(app_session, organization_id=user.organization_id)
        receipt = await receipt_service.create_goods_receipt(GoodsReceiptCreateRequest(
            purchase_order_id=po.id, warehouse_id=warehouse.id,
            items=[GoodsReceiptItemInput(purchase_order_item_id=po_item.id, product_id=product.id, quantity_received=10)],
        ))
        await receipt_service.complete_receipt(receipt.id, user_id=user.id)

        refreshed_po = await po_service.get_purchase_order(po.id)
        assert refreshed_po.status.value == "partially_received"

        receipt2 = await receipt_service.create_goods_receipt(GoodsReceiptCreateRequest(
            purchase_order_id=po.id, warehouse_id=warehouse.id,
            items=[GoodsReceiptItemInput(purchase_order_item_id=po_item.id, product_id=product.id, quantity_received=10)],
        ))
        await receipt_service.complete_receipt(receipt2.id, user_id=user.id)

        fully_received_po = await po_service.get_purchase_order(po.id)
        assert fully_received_po.status.value == "received"
        assert fully_received_po.received_at is not None

    asyncio.run(_run())


def test_cannot_complete_receipt_with_no_items(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = GoodsReceiptService(app_session, organization_id=user.organization_id)
        receipt = await service.create_goods_receipt(GoodsReceiptCreateRequest(warehouse_id=warehouse.id))

        with pytest.raises(HTTPException) as exc_info:
            await service.complete_receipt(receipt.id, user_id=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_cannot_complete_twice(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = GoodsReceiptService(app_session, organization_id=user.organization_id)
        receipt = await service.create_goods_receipt(GoodsReceiptCreateRequest(
            warehouse_id=warehouse.id, items=[GoodsReceiptItemInput(product_id=product.id, quantity_received=5)],
        ))
        await service.complete_receipt(receipt.id, user_id=user.id)

        with pytest.raises(HTTPException) as exc_info:
            await service.complete_receipt(receipt.id, user_id=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_cancel_receipt(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = GoodsReceiptService(app_session, organization_id=user.organization_id)
        receipt = await service.create_goods_receipt(GoodsReceiptCreateRequest(warehouse_id=warehouse.id))

        cancelled = await service.cancel_receipt(receipt.id)
        assert cancelled.status.value == "cancelled"

        with pytest.raises(HTTPException) as exc_info:
            await service.complete_receipt(receipt.id, user_id=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_add_and_remove_item_while_draft(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = GoodsReceiptService(app_session, organization_id=user.organization_id)
        receipt = await service.create_goods_receipt(GoodsReceiptCreateRequest(warehouse_id=warehouse.id))

        item = await service.add_item(receipt.id, GoodsReceiptItemInput(product_id=product.id, quantity_received=3))
        items = await service.get_items(receipt.id)
        assert len(items) == 1

        await service.remove_item(receipt.id, item.id)
        items_after = await service.get_items(receipt.id)
        assert len(items_after) == 0

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        product_a, warehouse_a = await _setup_product_and_warehouse(app_session, user_a.organization_id, user_a.id)

        service_a = GoodsReceiptService(app_session, organization_id=user_a.organization_id)
        service_b = GoodsReceiptService(app_session, organization_id=user_b.organization_id)
        receipt = await service_a.create_goods_receipt(GoodsReceiptCreateRequest(
            warehouse_id=warehouse_a.id, items=[GoodsReceiptItemInput(product_id=product_a.id, quantity_received=5)],
        ))

        assert await service_b.get_receipt(receipt.id) is None

    asyncio.run(_run())
