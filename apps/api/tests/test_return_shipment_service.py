import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.customer import CustomerCreateRequest
from app.schemas.order import OrderAddressInput, OrderCreateRequest, OrderLineItemInput
from app.schemas.product import ProductCreateRequest
from app.schemas.product_price import ProductPriceCreateRequest
from app.schemas.return_request import ReturnItemInput, ReturnRequestCreateRequest
from app.schemas.return_shipment import ReturnShipmentCreateRequest, ReturnShipmentSchedulePickupRequest
from app.schemas.warehouse import WarehouseCreateRequest
from app.services.auth_service import AuthService
from app.services.customer_service import CustomerService
from app.services.order_service import OrderService
from app.services.pricing_service import PricingService
from app.services.product_service import ProductService
from app.services.return_service import ReturnService
from app.services.return_shipment_service import ReturnShipmentService
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
    return OrderAddressInput(first_name="Ada", last_name="Lovelace", line1="1 Main St", city="Metropolis", country="US", phone="555-0000")


async def _register_org(session, email="owner@example.com", org_name="Return Shipment Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _setup_approved_return(session, org_id, user_id):
    customer_service = CustomerService(session, organization_id=org_id)
    customer = await customer_service.create_customer(CustomerCreateRequest(email="shopper@example.com", first_name="S", last_name="H"), created_by=user_id)

    product_service = ProductService(session, organization_id=org_id)
    product = await product_service.create_product(ProductCreateRequest(name="Widget", sku="WID-1", track_inventory=False), created_by=user_id)
    product = await product_service.publish_product(product.id, actor_id=user_id)

    pricing_service = PricingService(session, organization_id=org_id)
    await pricing_service.create_price(ProductPriceCreateRequest(product_id=product.id, currency="USD", selling_price=25.0), created_by=user_id)

    order_service = OrderService(session, organization_id=org_id)
    order = await order_service.create_order(OrderCreateRequest(
        customer_id=customer.id, billing_address=_address(), shipping_address=_address(),
        items=[OrderLineItemInput(product_id=product.id, quantity=1)],
    ), created_by=user_id)
    order = await order_service.confirm_order(order.id, changed_by=user_id)
    order = await order_service.start_processing(order.id, changed_by=user_id)
    order = await order_service.pack_order(order.id, changed_by=user_id)
    order = await order_service.mark_ready_to_ship(order.id, changed_by=user_id)
    order = await order_service.ship_order(order.id, changed_by=user_id)
    order = await order_service.mark_out_for_delivery(order.id, changed_by=user_id)
    order = await order_service.deliver_order(order.id, changed_by=user_id)
    items = await order_service.get_items(order.id)

    return_service = ReturnService(session, organization_id=org_id)
    return_request = await return_service.create_return_request(ReturnRequestCreateRequest(
        order_id=order.id, reason_code="damaged", items=[ReturnItemInput(order_item_id=items[0].id, quantity=1)],
    ), customer_id=customer.id, created_by=user_id)
    return_request = await return_service.approve_return(return_request.id, changed_by=user_id)

    warehouse_service = WarehouseService(session, organization_id=org_id)
    warehouse = await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Returns WH", code="RET-WH"), created_by=user_id)

    return return_request, warehouse


def test_create_return_shipment_snapshots_pickup_address(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        return_request, warehouse = await _setup_approved_return(app_session, user.organization_id, user.id)

        service = ReturnShipmentService(app_session, organization_id=user.organization_id)
        return_shipment = await service.create_return_shipment(ReturnShipmentCreateRequest(
            return_request_id=return_request.id, warehouse_id=warehouse.id,
        ), created_by=user.id)

        assert return_shipment.return_shipment_number.startswith("RS-")
        assert return_shipment.pickup_city == "Metropolis"
        assert return_shipment.pickup_contact_phone == "555-0000"
        assert return_shipment.status.value == "pending"

    asyncio.run(_run())


def test_cannot_create_return_shipment_for_unapproved_request(app_session: AsyncSession):
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
        order = await order_service.confirm_order(order.id, changed_by=user.id)
        order = await order_service.start_processing(order.id, changed_by=user.id)
        order = await order_service.pack_order(order.id, changed_by=user.id)
        order = await order_service.mark_ready_to_ship(order.id, changed_by=user.id)
        order = await order_service.ship_order(order.id, changed_by=user.id)
        order = await order_service.mark_out_for_delivery(order.id, changed_by=user.id)
        order = await order_service.deliver_order(order.id, changed_by=user.id)
        items = await order_service.get_items(order.id)

        return_service = ReturnService(app_session, organization_id=user.organization_id)
        return_request = await return_service.create_return_request(ReturnRequestCreateRequest(
            order_id=order.id, reason_code="damaged", items=[ReturnItemInput(order_item_id=items[0].id, quantity=1)],
        ), customer_id=customer.id, created_by=user.id)

        warehouse_service = WarehouseService(app_session, organization_id=user.organization_id)
        warehouse = await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Returns WH", code="RET-WH"), created_by=user.id)

        service = ReturnShipmentService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await service.create_return_shipment(ReturnShipmentCreateRequest(
                return_request_id=return_request.id, warehouse_id=warehouse.id,
            ), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_full_return_shipment_lifecycle_syncs_return_request(app_session: AsyncSession):
    async def _run():
        from datetime import datetime, timedelta

        user = await _register_org(app_session)
        return_request, warehouse = await _setup_approved_return(app_session, user.organization_id, user.id)

        service = ReturnShipmentService(app_session, organization_id=user.organization_id)
        return_shipment = await service.create_return_shipment(ReturnShipmentCreateRequest(
            return_request_id=return_request.id, warehouse_id=warehouse.id,
        ), created_by=user.id)

        return_shipment = await service.generate_label(return_shipment.id)
        assert return_shipment.tracking_number is not None

        return_shipment = await service.schedule_reverse_pickup(return_shipment.id, ReturnShipmentSchedulePickupRequest(scheduled_at=datetime.utcnow() + timedelta(days=1)))
        assert return_shipment.status.value == "reverse_pickup_scheduled"

        return_shipment = await service.mark_in_transit(return_shipment.id)
        return_shipment = await service.mark_received(return_shipment.id)
        assert return_shipment.status.value == "received"
        assert return_shipment.received_at is not None

        return_service = ReturnService(app_session, organization_id=user.organization_id)
        refreshed_return = await return_service.get_return(return_request.id)
        assert refreshed_return.status.value == "received"

    asyncio.run(_run())


def test_duplicate_return_shipment_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        return_request, warehouse = await _setup_approved_return(app_session, user.organization_id, user.id)

        service = ReturnShipmentService(app_session, organization_id=user.organization_id)
        await service.create_return_shipment(ReturnShipmentCreateRequest(return_request_id=return_request.id, warehouse_id=warehouse.id), created_by=user.id)

        with pytest.raises(HTTPException) as exc_info:
            await service.create_return_shipment(ReturnShipmentCreateRequest(return_request_id=return_request.id, warehouse_id=warehouse.id), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_cancel_return_shipment(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        return_request, warehouse = await _setup_approved_return(app_session, user.organization_id, user.id)

        service = ReturnShipmentService(app_session, organization_id=user.organization_id)
        return_shipment = await service.create_return_shipment(ReturnShipmentCreateRequest(return_request_id=return_request.id, warehouse_id=warehouse.id), created_by=user.id)

        cancelled = await service.cancel_return_shipment(return_shipment.id, reason="Customer withdrew return")
        assert cancelled.status.value == "cancelled"

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        return_request, warehouse = await _setup_approved_return(app_session, user_a.organization_id, user_a.id)

        service_a = ReturnShipmentService(app_session, organization_id=user_a.organization_id)
        service_b = ReturnShipmentService(app_session, organization_id=user_b.organization_id)
        return_shipment = await service_a.create_return_shipment(ReturnShipmentCreateRequest(return_request_id=return_request.id, warehouse_id=warehouse.id), created_by=user_a.id)

        assert await service_b.get_return_shipment(return_shipment.id) is None

    asyncio.run(_run())

