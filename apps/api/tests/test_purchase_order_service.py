import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.product import ProductCreateRequest
from app.schemas.purchase_order import (
    PurchaseOrderCreateRequest,
    PurchaseOrderLineItemInput,
    PurchaseOrderUpdateRequest,
)
from app.schemas.warehouse import WarehouseCreateRequest
from app.services.auth_service import AuthService
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


async def _register_org(session, email="owner@example.com", org_name="PO Test Org"):
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


def test_create_purchase_order_computes_totals(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = PurchaseOrderService(app_session, organization_id=user.organization_id)

        po = await service.create_purchase_order(PurchaseOrderCreateRequest(
            supplier_name="Acme Supplies", warehouse_id=warehouse.id, tax_amount=10, shipping_amount=5,
            items=[PurchaseOrderLineItemInput(product_id=product.id, quantity_ordered=10, unit_cost=2.5)],
        ), created_by=user.id)

        assert po.subtotal == 25.0
        assert po.total == 40.0
        assert po.status.value == "draft"
        assert po.po_number.startswith("PO-")

    asyncio.run(_run())


def test_duplicate_po_number_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = PurchaseOrderService(app_session, organization_id=user.organization_id)
        await service.create_purchase_order(PurchaseOrderCreateRequest(po_number="PO-FIXED", supplier_name="Acme", warehouse_id=warehouse.id), created_by=user.id)
        with pytest.raises(HTTPException) as exc_info:
            await service.create_purchase_order(PurchaseOrderCreateRequest(po_number="PO-FIXED", supplier_name="Acme", warehouse_id=warehouse.id), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_send_requires_items(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = PurchaseOrderService(app_session, organization_id=user.organization_id)
        po = await service.create_purchase_order(PurchaseOrderCreateRequest(supplier_name="Acme", warehouse_id=warehouse.id), created_by=user.id)

        with pytest.raises(HTTPException) as exc_info:
            await service.send_purchase_order(po.id)
        assert exc_info.value.status_code == 400

        await service.add_item(po.id, PurchaseOrderLineItemInput(product_id=product.id, quantity_ordered=5, unit_cost=1))
        sent = await service.send_purchase_order(po.id)
        assert sent.status.value == "sent"
        assert sent.sent_at is not None

    asyncio.run(_run())


def test_cannot_send_twice(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = PurchaseOrderService(app_session, organization_id=user.organization_id)
        po = await service.create_purchase_order(PurchaseOrderCreateRequest(
            supplier_name="Acme", warehouse_id=warehouse.id,
            items=[PurchaseOrderLineItemInput(product_id=product.id, quantity_ordered=5, unit_cost=1)],
        ), created_by=user.id)
        await service.send_purchase_order(po.id)

        with pytest.raises(HTTPException) as exc_info:
            await service.send_purchase_order(po.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_cancel_purchase_order(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = PurchaseOrderService(app_session, organization_id=user.organization_id)
        po = await service.create_purchase_order(PurchaseOrderCreateRequest(supplier_name="Acme", warehouse_id=warehouse.id), created_by=user.id)

        cancelled = await service.cancel_purchase_order(po.id)
        assert cancelled.status.value == "cancelled"

        with pytest.raises(HTTPException) as exc_info:
            await service.cancel_purchase_order(po.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_add_and_remove_item_recomputes_totals(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = PurchaseOrderService(app_session, organization_id=user.organization_id)
        po = await service.create_purchase_order(PurchaseOrderCreateRequest(supplier_name="Acme", warehouse_id=warehouse.id), created_by=user.id)

        item = await service.add_item(po.id, PurchaseOrderLineItemInput(product_id=product.id, quantity_ordered=4, unit_cost=3))
        refreshed = await service.get_purchase_order(po.id)
        assert refreshed.subtotal == 12.0

        await service.remove_item(po.id, item.id)
        refreshed_after = await service.get_purchase_order(po.id)
        assert refreshed_after.subtotal == 0.0

    asyncio.run(_run())


def test_update_purchase_order(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = PurchaseOrderService(app_session, organization_id=user.organization_id)
        po = await service.create_purchase_order(PurchaseOrderCreateRequest(supplier_name="Acme", warehouse_id=warehouse.id), created_by=user.id)

        updated = await service.update_purchase_order(po.id, PurchaseOrderUpdateRequest(supplier_name="New Supplier", shipping_amount=20))
        assert updated.supplier_name == "New Supplier"
        assert updated.total == 20.0

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        product_a, warehouse_a = await _setup_product_and_warehouse(app_session, user_a.organization_id, user_a.id)

        service_a = PurchaseOrderService(app_session, organization_id=user_a.organization_id)
        service_b = PurchaseOrderService(app_session, organization_id=user_b.organization_id)
        po = await service_a.create_purchase_order(PurchaseOrderCreateRequest(supplier_name="Acme", warehouse_id=warehouse_a.id), created_by=user_a.id)

        assert await service_b.get_purchase_order(po.id) is None

    asyncio.run(_run())
