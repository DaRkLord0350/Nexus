import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.models.inventory_transaction import InventoryTransactionType
from app.models.return_item import ReturnItemCondition
from app.schemas.customer import CustomerCreateRequest
from app.schemas.order import OrderAddressInput, OrderCreateRequest, OrderLineItemInput
from app.schemas.product import ProductCreateRequest
from app.schemas.product_price import ProductPriceCreateRequest
from app.schemas.return_request import (
    ReturnCompleteRequest,
    ReturnItemInput,
    ReturnRequestCreateRequest,
    ReturnResolution,
)
from app.schemas.warehouse import WarehouseCreateRequest
from app.services.auth_service import AuthService
from app.services.customer_service import CustomerService
from app.services.order_service import OrderService
from app.services.pricing_service import PricingService
from app.services.product_service import ProductService
from app.services.return_service import ReturnService
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


def _address() -> OrderAddressInput:
    return OrderAddressInput(first_name="Ada", last_name="Lovelace", line1="1 Main St", city="Metropolis", country="US")


async def _register_org(session, email="owner@example.com", org_name="Return Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _setup_delivered_order(session, org_id, user_id, price=50.0, quantity=2, warehouse_id=None):
    customer_service = CustomerService(session, organization_id=org_id)
    customer = await customer_service.create_customer(CustomerCreateRequest(email="shopper@example.com", first_name="S", last_name="H"), created_by=user_id)

    product_service = ProductService(session, organization_id=org_id)
    product = await product_service.create_product(ProductCreateRequest(name="Widget", sku="WID-1", track_inventory=warehouse_id is not None), created_by=user_id)
    product = await product_service.publish_product(product.id, actor_id=user_id)

    pricing_service = PricingService(session, organization_id=org_id)
    await pricing_service.create_price(ProductPriceCreateRequest(product_id=product.id, currency="USD", selling_price=price), created_by=user_id)

    if warehouse_id:
        stock_service = StockMovementService(session, organization_id=org_id)
        await stock_service.apply_movement(
            product_id=product.id, variant_id=None, warehouse_id=warehouse_id,
            transaction_type=InventoryTransactionType.adjustment, quantity_delta=100, field="quantity_available",
        )

    order_service = OrderService(session, organization_id=org_id)
    order = await order_service.create_order(OrderCreateRequest(
        customer_id=customer.id, billing_address=_address(), shipping_address=_address(),
        items=[OrderLineItemInput(product_id=product.id, quantity=quantity, warehouse_id=warehouse_id)],
    ), created_by=user_id)

    order = await order_service.confirm_order(order.id, changed_by=user_id)
    order = await order_service.start_processing(order.id, changed_by=user_id)
    order = await order_service.pack_order(order.id, changed_by=user_id)
    order = await order_service.mark_ready_to_ship(order.id, changed_by=user_id)
    order = await order_service.ship_order(order.id, changed_by=user_id)
    order = await order_service.mark_out_for_delivery(order.id, changed_by=user_id)
    order = await order_service.deliver_order(order.id, changed_by=user_id)

    items = await order_service.get_items(order.id)
    return order, customer, items[0], product


def test_create_return_request_requires_delivered_order(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        customer_service = CustomerService(app_session, organization_id=user.organization_id)
        customer = await customer_service.create_customer(CustomerCreateRequest(email="c@example.com", first_name="C", last_name="D"), created_by=user.id)
        product_service = ProductService(app_session, organization_id=user.organization_id)
        product = await product_service.create_product(ProductCreateRequest(name="Widget", sku="WID-2", track_inventory=False), created_by=user.id)
        product = await product_service.publish_product(product.id, actor_id=user.id)
        pricing_service = PricingService(app_session, organization_id=user.organization_id)
        await pricing_service.create_price(ProductPriceCreateRequest(product_id=product.id, currency="USD", selling_price=10), created_by=user.id)

        order_service = OrderService(app_session, organization_id=user.organization_id)
        order = await order_service.create_order(OrderCreateRequest(
            customer_id=customer.id, billing_address=_address(), shipping_address=_address(),
            items=[OrderLineItemInput(product_id=product.id, quantity=1)],
        ), created_by=user.id)

        return_service = ReturnService(app_session, organization_id=user.organization_id)
        items = await order_service.get_items(order.id)
        with pytest.raises(HTTPException) as exc_info:
            await return_service.create_return_request(ReturnRequestCreateRequest(
                order_id=order.id, reason_code="damaged", items=[ReturnItemInput(order_item_id=items[0].id, quantity=1)],
            ), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_full_return_lifecycle_restocks_sellable_condition(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        warehouse_service = WarehouseService(app_session, organization_id=user.organization_id)
        warehouse = await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Main", code="MAIN"), created_by=user.id)

        order, customer, order_item, product = await _setup_delivered_order(app_session, user.organization_id, user.id, price=25.0, quantity=3, warehouse_id=warehouse.id)

        return_service = ReturnService(app_session, organization_id=user.organization_id)
        return_request = await return_service.create_return_request(ReturnRequestCreateRequest(
            order_id=order.id, reason_code="wrong_item", items=[ReturnItemInput(order_item_id=order_item.id, quantity=2)],
        ), customer_id=customer.id, created_by=user.id)
        assert return_request.status.value == "requested"
        assert return_request.return_number.startswith("RET-")

        return_request = await return_service.approve_return(return_request.id, changed_by=user.id)
        assert return_request.status.value == "approved"

        return_request = await return_service.mark_received(return_request.id, warehouse_id=warehouse.id)
        assert return_request.status.value == "received"

        return_request = await return_service.start_inspection(return_request.id, changed_by=user.id)
        items = await return_service.get_items(return_request.id)
        await return_service.update_item_inspection(return_request.id, items[0].id, condition=ReturnItemCondition.unopened)

        from app.repositories.inventory_repository import InventoryRepository
        inventory_repo = InventoryRepository(app_session, organization_id=user.organization_id)
        before_row = await inventory_repo.find_one(product.id, None, warehouse.id)
        before_qty = before_row.quantity_available

        return_request = await return_service.complete_return(return_request.id, resolution=ReturnResolution.refund, restock=True, changed_by=user.id)
        assert return_request.status.value == "completed"
        assert return_request.resolution.value == "refund"

        await app_session.refresh(before_row)
        assert before_row.quantity_available == before_qty + 2

        from app.repositories.order_repository import OrderItemRepository
        item_repo = OrderItemRepository(app_session, organization_id=user.organization_id)
        refreshed_order_item = await item_repo.get_by_id(order_item.id)
        assert refreshed_order_item.quantity_returned == 2

    asyncio.run(_run())


def test_damaged_condition_goes_to_damaged_stock(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        warehouse_service = WarehouseService(app_session, organization_id=user.organization_id)
        warehouse = await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Main", code="MAIN"), created_by=user.id)

        order, customer, order_item, product = await _setup_delivered_order(app_session, user.organization_id, user.id, price=25.0, quantity=1, warehouse_id=warehouse.id)

        return_service = ReturnService(app_session, organization_id=user.organization_id)
        return_request = await return_service.create_return_request(ReturnRequestCreateRequest(
            order_id=order.id, reason_code="damaged", items=[ReturnItemInput(order_item_id=order_item.id, quantity=1)],
        ), customer_id=customer.id, created_by=user.id)
        await return_service.approve_return(return_request.id, changed_by=user.id)
        await return_service.mark_received(return_request.id, warehouse_id=warehouse.id)
        await return_service.start_inspection(return_request.id, changed_by=user.id)
        items = await return_service.get_items(return_request.id)
        await return_service.update_item_inspection(return_request.id, items[0].id, condition=ReturnItemCondition.damaged)

        from app.repositories.inventory_repository import InventoryRepository
        inventory_repo = InventoryRepository(app_session, organization_id=user.organization_id)
        before_row = await inventory_repo.find_one(product.id, None, warehouse.id)
        before_available = before_row.quantity_available
        before_damaged = before_row.quantity_damaged

        await return_service.complete_return(return_request.id, resolution=ReturnResolution.refund, restock=True, changed_by=user.id)

        await app_session.refresh(before_row)
        assert before_row.quantity_available == before_available  # not resold
        assert before_row.quantity_damaged == before_damaged + 1

    asyncio.run(_run())


def test_cannot_return_more_than_purchased(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order, customer, order_item, product = await _setup_delivered_order(app_session, user.organization_id, user.id, price=10.0, quantity=1)

        return_service = ReturnService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await return_service.create_return_request(ReturnRequestCreateRequest(
                order_id=order.id, reason_code="damaged", items=[ReturnItemInput(order_item_id=order_item.id, quantity=5)],
            ), customer_id=customer.id, created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_reject_return(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order, customer, order_item, product = await _setup_delivered_order(app_session, user.organization_id, user.id)

        return_service = ReturnService(app_session, organization_id=user.organization_id)
        return_request = await return_service.create_return_request(ReturnRequestCreateRequest(
            order_id=order.id, reason_code="no_longer_needed", items=[ReturnItemInput(order_item_id=order_item.id, quantity=1)],
        ), customer_id=customer.id, created_by=user.id)

        rejected = await return_service.reject_return(return_request.id, changed_by=user.id, reason="Outside return window")
        assert rejected.status.value == "rejected"
        assert rejected.rejected_reason == "Outside return window"

        with pytest.raises(HTTPException) as exc_info:
            await return_service.approve_return(return_request.id, changed_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_cancel_return(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order, customer, order_item, product = await _setup_delivered_order(app_session, user.organization_id, user.id)

        return_service = ReturnService(app_session, organization_id=user.organization_id)
        return_request = await return_service.create_return_request(ReturnRequestCreateRequest(
            order_id=order.id, reason_code="no_longer_needed", items=[ReturnItemInput(order_item_id=order_item.id, quantity=1)],
        ), customer_id=customer.id, created_by=user.id)

        cancelled = await return_service.cancel_return(return_request.id, reason="Customer changed mind")
        assert cancelled.status.value == "cancelled"

    asyncio.run(_run())


def test_return_for_wrong_customer_forbidden(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order, customer, order_item, product = await _setup_delivered_order(app_session, user.organization_id, user.id)

        other_customer_service = CustomerService(app_session, organization_id=user.organization_id)
        other_customer = await other_customer_service.create_customer(CustomerCreateRequest(email="other@example.com", first_name="O", last_name="P"), created_by=user.id)

        return_service = ReturnService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await return_service.create_return_request(ReturnRequestCreateRequest(
                order_id=order.id, reason_code="damaged", items=[ReturnItemInput(order_item_id=order_item.id, quantity=1)],
            ), customer_id=other_customer.id, created_by=user.id)
        assert exc_info.value.status_code == 403

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        order, customer, order_item, product = await _setup_delivered_order(app_session, user_a.organization_id, user_a.id)

        return_service_a = ReturnService(app_session, organization_id=user_a.organization_id)
        return_service_b = ReturnService(app_session, organization_id=user_b.organization_id)
        return_request = await return_service_a.create_return_request(ReturnRequestCreateRequest(
            order_id=order.id, reason_code="damaged", items=[ReturnItemInput(order_item_id=order_item.id, quantity=1)],
        ), customer_id=customer.id, created_by=user_a.id)

        assert await return_service_b.get_return(return_request.id) is None

    asyncio.run(_run())

