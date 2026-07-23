import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.customer import CustomerCreateRequest
from app.schemas.order import OrderAddressInput, OrderCreateRequest, OrderLineItemInput
from app.schemas.pickup import PickupCreateRequest, PickupRescheduleRequest
from app.schemas.product import ProductCreateRequest
from app.schemas.product_price import ProductPriceCreateRequest
from app.schemas.shipment import ShipmentCreateRequest, ShipmentItemInput
from app.schemas.warehouse import WarehouseCreateRequest
from app.services.auth_service import AuthService
from app.services.customer_service import CustomerService
from app.services.order_service import OrderService
from app.services.pickup_service import PickupService
from app.services.pricing_service import PricingService
from app.services.product_service import ProductService
from app.services.shipment_service import ShipmentService
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


async def _register_org(session, email="owner@example.com", org_name="Pickup Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _setup_shipment(session, org_id, user_id, suffix="1"):
    customer_service = CustomerService(session, organization_id=org_id)
    customer = await customer_service.create_customer(CustomerCreateRequest(email=f"shopper{suffix}@example.com", first_name="S", last_name="H"), created_by=user_id)

    product_service = ProductService(session, organization_id=org_id)
    product = await product_service.create_product(ProductCreateRequest(name=f"Widget {suffix}", sku=f"WID-{suffix}", track_inventory=False), created_by=user_id)
    product = await product_service.publish_product(product.id, actor_id=user_id)

    pricing_service = PricingService(session, organization_id=org_id)
    await pricing_service.create_price(ProductPriceCreateRequest(product_id=product.id, currency="USD", selling_price=25.0), created_by=user_id)

    order_service = OrderService(session, organization_id=org_id)
    order = await order_service.create_order(OrderCreateRequest(
        customer_id=customer.id, billing_address=_address(), shipping_address=_address(),
        items=[OrderLineItemInput(product_id=product.id, quantity=1)],
    ), created_by=user_id)
    order = await order_service.confirm_order(order.id, changed_by=user_id)
    items = await order_service.get_items(order.id)
    return order, items[0]


async def _setup_warehouse(session, org_id, user_id, suffix="1"):
    warehouse_service = WarehouseService(session, organization_id=org_id)
    return await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Main", code=f"MAIN-{suffix}"), created_by=user_id)


def test_schedule_pickup_links_shipments(app_session: AsyncSession):
    async def _run():
        from datetime import datetime, timedelta

        user = await _register_org(app_session)
        warehouse = await _setup_warehouse(app_session, user.organization_id, user.id)
        order, order_item = await _setup_shipment(app_session, user.organization_id, user.id)

        shipment_service = ShipmentService(app_session, organization_id=user.organization_id)
        shipment = await shipment_service.create_shipment(ShipmentCreateRequest(
            order_id=order.id, warehouse_id=warehouse.id, items=[ShipmentItemInput(order_item_id=order_item.id, quantity=1)],
        ), created_by=user.id)

        pickup_service = PickupService(app_session, organization_id=user.organization_id)
        pickup = await pickup_service.schedule_pickup(PickupCreateRequest(
            warehouse_id=warehouse.id, scheduled_date=datetime.utcnow() + timedelta(days=1), shipment_ids=[shipment.id],
        ), created_by=user.id)

        assert pickup.pickup_number.startswith("PU-")
        assert pickup.status.value == "scheduled"

        linked = await pickup_service.get_shipments(pickup.id)
        assert len(linked) == 1
        assert linked[0].id == shipment.id

    asyncio.run(_run())


def test_schedule_pickup_rejects_mismatched_warehouse(app_session: AsyncSession):
    async def _run():
        from datetime import datetime, timedelta

        user = await _register_org(app_session)
        warehouse_a = await _setup_warehouse(app_session, user.organization_id, user.id, suffix="a")
        warehouse_b = await _setup_warehouse(app_session, user.organization_id, user.id, suffix="b")
        order, order_item = await _setup_shipment(app_session, user.organization_id, user.id)

        shipment_service = ShipmentService(app_session, organization_id=user.organization_id)
        shipment = await shipment_service.create_shipment(ShipmentCreateRequest(
            order_id=order.id, warehouse_id=warehouse_a.id, items=[ShipmentItemInput(order_item_id=order_item.id, quantity=1)],
        ), created_by=user.id)

        pickup_service = PickupService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await pickup_service.schedule_pickup(PickupCreateRequest(
                warehouse_id=warehouse_b.id, scheduled_date=datetime.utcnow() + timedelta(days=1), shipment_ids=[shipment.id],
            ), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_full_pickup_lifecycle(app_session: AsyncSession):
    async def _run():
        from datetime import datetime, timedelta

        user = await _register_org(app_session)
        warehouse = await _setup_warehouse(app_session, user.organization_id, user.id)
        order, order_item = await _setup_shipment(app_session, user.organization_id, user.id)

        shipment_service = ShipmentService(app_session, organization_id=user.organization_id)
        shipment = await shipment_service.create_shipment(ShipmentCreateRequest(
            order_id=order.id, warehouse_id=warehouse.id, items=[ShipmentItemInput(order_item_id=order_item.id, quantity=1)],
        ), created_by=user.id)
        await shipment_service.generate_label(shipment.id)

        pickup_service = PickupService(app_session, organization_id=user.organization_id)
        pickup = await pickup_service.schedule_pickup(PickupCreateRequest(
            warehouse_id=warehouse.id, scheduled_date=datetime.utcnow() + timedelta(days=1), shipment_ids=[shipment.id],
        ), created_by=user.id)

        pickup = await pickup_service.confirm_pickup(pickup.id)
        assert pickup.status.value == "confirmed"

        pickup = await pickup_service.complete_pickup(pickup.id)
        assert pickup.status.value == "completed"
        assert pickup.completed_at is not None

        refreshed_shipment = await shipment_service.get_shipment(shipment.id)
        assert refreshed_shipment.status.value == "picked_up"

    asyncio.run(_run())


def test_reschedule_pickup(app_session: AsyncSession):
    async def _run():
        from datetime import datetime, timedelta

        user = await _register_org(app_session)
        warehouse = await _setup_warehouse(app_session, user.organization_id, user.id)

        pickup_service = PickupService(app_session, organization_id=user.organization_id)
        pickup = await pickup_service.schedule_pickup(PickupCreateRequest(
            warehouse_id=warehouse.id, scheduled_date=datetime.utcnow() + timedelta(days=1),
        ), created_by=user.id)

        new_date = datetime.utcnow() + timedelta(days=3)
        rescheduled = await pickup_service.reschedule_pickup(pickup.id, PickupRescheduleRequest(scheduled_date=new_date, time_slot="14:00-18:00"))
        assert rescheduled.time_slot == "14:00-18:00"

    asyncio.run(_run())


def test_cancel_pickup_unlinks_shipments(app_session: AsyncSession):
    async def _run():
        from datetime import datetime, timedelta

        user = await _register_org(app_session)
        warehouse = await _setup_warehouse(app_session, user.organization_id, user.id)
        order, order_item = await _setup_shipment(app_session, user.organization_id, user.id)

        shipment_service = ShipmentService(app_session, organization_id=user.organization_id)
        shipment = await shipment_service.create_shipment(ShipmentCreateRequest(
            order_id=order.id, warehouse_id=warehouse.id, items=[ShipmentItemInput(order_item_id=order_item.id, quantity=1)],
        ), created_by=user.id)

        pickup_service = PickupService(app_session, organization_id=user.organization_id)
        pickup = await pickup_service.schedule_pickup(PickupCreateRequest(
            warehouse_id=warehouse.id, scheduled_date=datetime.utcnow() + timedelta(days=1), shipment_ids=[shipment.id],
        ), created_by=user.id)

        cancelled = await pickup_service.cancel_pickup(pickup.id, reason="Carrier holiday")
        assert cancelled.status.value == "cancelled"

        linked = await pickup_service.shipment_repo.list_for_pickup(pickup.id)
        assert linked == []

    asyncio.run(_run())


def test_invalid_transition_rejected(app_session: AsyncSession):
    async def _run():
        from datetime import datetime, timedelta

        user = await _register_org(app_session)
        warehouse = await _setup_warehouse(app_session, user.organization_id, user.id)

        pickup_service = PickupService(app_session, organization_id=user.organization_id)
        pickup = await pickup_service.schedule_pickup(PickupCreateRequest(
            warehouse_id=warehouse.id, scheduled_date=datetime.utcnow() + timedelta(days=1),
        ), created_by=user.id)

        with pytest.raises(HTTPException) as exc_info:
            await pickup_service.complete_pickup(pickup.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        from datetime import datetime, timedelta

        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        warehouse = await _setup_warehouse(app_session, user_a.organization_id, user_a.id)

        pickup_service_a = PickupService(app_session, organization_id=user_a.organization_id)
        pickup_service_b = PickupService(app_session, organization_id=user_b.organization_id)
        pickup = await pickup_service_a.schedule_pickup(PickupCreateRequest(
            warehouse_id=warehouse.id, scheduled_date=datetime.utcnow() + timedelta(days=1),
        ), created_by=user_a.id)

        assert await pickup_service_b.get_pickup(pickup.id) is None

    asyncio.run(_run())

