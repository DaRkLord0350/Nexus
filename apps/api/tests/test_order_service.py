import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.models.inventory_transaction import InventoryTransactionType
from app.schemas.coupon import CouponCreateRequest, CouponDiscountType
from app.schemas.customer import CustomerCreateRequest
from app.schemas.order import OrderAddressInput, OrderCreateRequest, OrderLineItemInput, OrderUpdateRequest
from app.schemas.product import ProductCreateRequest
from app.schemas.product_price import ProductPriceCreateRequest
from app.schemas.warehouse import WarehouseCreateRequest
from app.services.auth_service import AuthService
from app.services.coupon_service import CouponService
from app.services.customer_service import CustomerService
from app.services.order_service import OrderService
from app.services.pricing_service import PricingService
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


def _address() -> OrderAddressInput:
    return OrderAddressInput(first_name="Ada", last_name="Lovelace", line1="1 Main St", city="Metropolis", country="US")


async def _register_org(session, email="owner@example.com", org_name="Order Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _setup_customer(session, org_id, user_id, email="shopper@example.com"):
    customer_service = CustomerService(session, organization_id=org_id)
    return await customer_service.create_customer(CustomerCreateRequest(email=email, first_name="S", last_name="H"), created_by=user_id)


async def _setup_published_product(session, org_id, user_id, price: float = 25.0, track_inventory: bool = False, sku: str = "WID-1"):
    product_service = ProductService(session, organization_id=org_id)
    product = await product_service.create_product(ProductCreateRequest(name="Widget", sku=sku, track_inventory=track_inventory), created_by=user_id)
    product = await product_service.publish_product(product.id, actor_id=user_id)

    pricing_service = PricingService(session, organization_id=org_id)
    await pricing_service.create_price(ProductPriceCreateRequest(product_id=product.id, currency="USD", selling_price=price), created_by=user_id)
    return product


async def _setup_warehouse_with_stock(session, org_id, user_id, product_id, quantity: int):
    warehouse_service = WarehouseService(session, organization_id=org_id)
    warehouse = await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Main", code="MAIN"), created_by=user_id)
    stock_service = StockMovementService(session, organization_id=org_id)
    await stock_service.apply_movement(
        product_id=product_id, variant_id=None, warehouse_id=warehouse.id,
        transaction_type=InventoryTransactionType.adjustment, quantity_delta=quantity, field="quantity_available",
    )
    return warehouse


def test_create_order_computes_totals(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        customer = await _setup_customer(app_session, user.organization_id, user.id)
        product = await _setup_published_product(app_session, user.organization_id, user.id, price=25.0)
        service = OrderService(app_session, organization_id=user.organization_id)

        order = await service.create_order(OrderCreateRequest(
            customer_id=customer.id, billing_address=_address(), shipping_address=_address(),
            shipping_amount=5, items=[OrderLineItemInput(product_id=product.id, quantity=2)],
        ), created_by=user.id)

        assert order.subtotal == 50.0
        assert order.total == 55.0
        assert order.status.value == "pending"
        assert order.order_number.startswith("ORD-")
        assert order.placed_at is not None

    asyncio.run(_run())


def test_create_order_without_items_is_draft(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        customer = await _setup_customer(app_session, user.organization_id, user.id)
        service = OrderService(app_session, organization_id=user.organization_id)

        order = await service.create_order(OrderCreateRequest(
            customer_id=customer.id, billing_address=_address(), shipping_address=_address(),
        ), created_by=user.id)

        assert order.status.value == "draft"
        assert order.placed_at is None

    asyncio.run(_run())


def test_create_order_deducts_stock_and_rejects_insufficient(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        customer = await _setup_customer(app_session, user.organization_id, user.id)
        product = await _setup_published_product(app_session, user.organization_id, user.id, price=10.0, track_inventory=True)
        warehouse = await _setup_warehouse_with_stock(app_session, user.organization_id, user.id, product.id, quantity=3)

        service = OrderService(app_session, organization_id=user.organization_id)

        with pytest.raises(HTTPException) as exc_info:
            await service.create_order(OrderCreateRequest(
                customer_id=customer.id, billing_address=_address(), shipping_address=_address(),
                items=[OrderLineItemInput(product_id=product.id, quantity=5, warehouse_id=warehouse.id)],
            ), created_by=user.id)
        assert exc_info.value.status_code == 400

        # No ghost order should have been created for the failed attempt.
        orders, total = await service.list_orders(customer_id=customer.id)
        assert total == 0

        order = await service.create_order(OrderCreateRequest(
            customer_id=customer.id, billing_address=_address(), shipping_address=_address(),
            items=[OrderLineItemInput(product_id=product.id, quantity=3, warehouse_id=warehouse.id)],
        ), created_by=user.id)
        assert order.total == 30.0

    asyncio.run(_run())


def test_apply_coupon_on_order(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        customer = await _setup_customer(app_session, user.organization_id, user.id)
        product = await _setup_published_product(app_session, user.organization_id, user.id, price=100.0)
        coupon_service = CouponService(app_session, organization_id=user.organization_id)
        await coupon_service.create_coupon(CouponCreateRequest(code="SAVE20", discount_type=CouponDiscountType.percentage, discount_value=20), created_by=user.id)

        service = OrderService(app_session, organization_id=user.organization_id)
        order = await service.create_order(OrderCreateRequest(
            customer_id=customer.id, billing_address=_address(), shipping_address=_address(), coupon_code="save20",
            items=[OrderLineItemInput(product_id=product.id, quantity=1)],
        ), created_by=user.id)

        assert order.discount_amount == 20.0
        assert order.total == 80.0

    asyncio.run(_run())


def test_status_workflow_happy_path(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        customer = await _setup_customer(app_session, user.organization_id, user.id)
        product = await _setup_published_product(app_session, user.organization_id, user.id)
        service = OrderService(app_session, organization_id=user.organization_id)
        order = await service.create_order(OrderCreateRequest(
            customer_id=customer.id, billing_address=_address(), shipping_address=_address(),
            items=[OrderLineItemInput(product_id=product.id, quantity=1)],
        ), created_by=user.id)

        order = await service.confirm_order(order.id, changed_by=user.id)
        assert order.status.value == "confirmed"
        order = await service.start_processing(order.id, changed_by=user.id)
        order = await service.pack_order(order.id, changed_by=user.id)
        order = await service.mark_ready_to_ship(order.id, changed_by=user.id)
        order = await service.ship_order(order.id, changed_by=user.id)
        order = await service.mark_out_for_delivery(order.id, changed_by=user.id)
        order = await service.deliver_order(order.id, changed_by=user.id)
        assert order.status.value == "delivered"
        assert order.delivered_at is not None

        history = await service.get_status_history(order.id)
        assert [entry.to_status for entry in history] == [
            "pending", "confirmed", "processing", "packed", "ready_to_ship", "shipped", "out_for_delivery", "delivered",
        ]

    asyncio.run(_run())


def test_invalid_transition_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        customer = await _setup_customer(app_session, user.organization_id, user.id)
        product = await _setup_published_product(app_session, user.organization_id, user.id)
        service = OrderService(app_session, organization_id=user.organization_id)
        order = await service.create_order(OrderCreateRequest(
            customer_id=customer.id, billing_address=_address(), shipping_address=_address(),
            items=[OrderLineItemInput(product_id=product.id, quantity=1)],
        ), created_by=user.id)

        with pytest.raises(HTTPException) as exc_info:
            await service.deliver_order(order.id, changed_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_hold_and_resume(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        customer = await _setup_customer(app_session, user.organization_id, user.id)
        product = await _setup_published_product(app_session, user.organization_id, user.id)
        service = OrderService(app_session, organization_id=user.organization_id)
        order = await service.create_order(OrderCreateRequest(
            customer_id=customer.id, billing_address=_address(), shipping_address=_address(),
            items=[OrderLineItemInput(product_id=product.id, quantity=1)],
        ), created_by=user.id)
        order = await service.confirm_order(order.id, changed_by=user.id)

        held = await service.hold_order(order.id, changed_by=user.id, reason="Fraud review")
        assert held.status.value == "hold"
        assert held.previous_status.value == "confirmed"

        resumed = await service.resume_order(order.id, changed_by=user.id)
        assert resumed.status.value == "confirmed"
        assert resumed.previous_status is None

    asyncio.run(_run())


def test_cancel_restocks_inventory(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        customer = await _setup_customer(app_session, user.organization_id, user.id)
        product = await _setup_published_product(app_session, user.organization_id, user.id, price=10.0, track_inventory=True)
        warehouse = await _setup_warehouse_with_stock(app_session, user.organization_id, user.id, product.id, quantity=10)

        service = OrderService(app_session, organization_id=user.organization_id)
        order = await service.create_order(OrderCreateRequest(
            customer_id=customer.id, billing_address=_address(), shipping_address=_address(),
            items=[OrderLineItemInput(product_id=product.id, quantity=4, warehouse_id=warehouse.id)],
        ), created_by=user.id)

        from app.repositories.inventory_repository import InventoryRepository
        inventory_repo = InventoryRepository(app_session, organization_id=user.organization_id)
        inventory = await inventory_repo.find_one(product.id, None, warehouse.id)
        assert inventory.quantity_available == 6

        cancelled = await service.cancel_order(order.id, changed_by=user.id, reason="Customer request")
        assert cancelled.status.value == "cancelled"

        inventory = await inventory_repo.find_one(product.id, None, warehouse.id)
        assert inventory.quantity_available == 10

    asyncio.run(_run())


def test_cannot_cancel_shipped_order(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        customer = await _setup_customer(app_session, user.organization_id, user.id)
        product = await _setup_published_product(app_session, user.organization_id, user.id)
        service = OrderService(app_session, organization_id=user.organization_id)
        order = await service.create_order(OrderCreateRequest(
            customer_id=customer.id, billing_address=_address(), shipping_address=_address(),
            items=[OrderLineItemInput(product_id=product.id, quantity=1)],
        ), created_by=user.id)
        order = await service.confirm_order(order.id, changed_by=user.id)
        order = await service.start_processing(order.id, changed_by=user.id)
        order = await service.pack_order(order.id, changed_by=user.id)
        order = await service.mark_ready_to_ship(order.id, changed_by=user.id)
        order = await service.ship_order(order.id, changed_by=user.id)

        with pytest.raises(HTTPException) as exc_info:
            await service.cancel_order(order.id, changed_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_add_note_and_update_order(app_session: AsyncSession):
    async def _run():
        from app.schemas.order import OrderNoteCreateRequest

        user = await _register_org(app_session)
        customer = await _setup_customer(app_session, user.organization_id, user.id)
        product = await _setup_published_product(app_session, user.organization_id, user.id)
        service = OrderService(app_session, organization_id=user.organization_id)
        order = await service.create_order(OrderCreateRequest(
            customer_id=customer.id, billing_address=_address(), shipping_address=_address(),
            items=[OrderLineItemInput(product_id=product.id, quantity=1)],
        ), created_by=user.id)

        note = await service.add_note(order.id, OrderNoteCreateRequest(note="Called customer to confirm address."), created_by=user.id)
        assert note.note.startswith("Called customer")

        updated = await service.update_order(order.id, OrderUpdateRequest(tags="vip,gift", requires_manual_review=True))
        assert updated.tags == "vip,gift"
        assert updated.requires_manual_review is True

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        customer_a = await _setup_customer(app_session, user_a.organization_id, user_a.id)
        product_a = await _setup_published_product(app_session, user_a.organization_id, user_a.id)

        service_a = OrderService(app_session, organization_id=user_a.organization_id)
        service_b = OrderService(app_session, organization_id=user_b.organization_id)
        order = await service_a.create_order(OrderCreateRequest(
            customer_id=customer_a.id, billing_address=_address(), shipping_address=_address(),
            items=[OrderLineItemInput(product_id=product_a.id, quantity=1)],
        ), created_by=user_a.id)

        assert await service_b.get_order(order.id) is None

    asyncio.run(_run())

