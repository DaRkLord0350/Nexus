import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.customer import CustomerCreateRequest
from app.schemas.order import OrderAddressInput, OrderCreateRequest, OrderLineItemInput
from app.schemas.product import ProductCreateRequest
from app.schemas.product_price import ProductPriceCreateRequest
from app.schemas.shipment import ShipmentCreateRequest, ShipmentItemInput
from app.schemas.shipping_provider import ShippingProviderCreateRequest
from app.schemas.warehouse import WarehouseCreateRequest
from app.services.auth_service import AuthService
from app.services.customer_service import CustomerService
from app.services.order_service import OrderService
from app.services.pricing_service import PricingService
from app.services.product_service import ProductService
from app.services.shipment_service import ShipmentService
from app.services.shipping_provider_service import ShippingProviderService
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
    return OrderAddressInput(first_name="Ada", last_name="Lovelace", line1="1 Main St", city="Metropolis", state="NY", country="US")


async def _register_org(session, email="owner@example.com", org_name="Shipment Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _setup_order(session, org_id, user_id, quantity=3):
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
        items=[OrderLineItemInput(product_id=product.id, quantity=quantity)],
    ), created_by=user_id)
    order = await order_service.confirm_order(order.id, changed_by=user_id)

    items = await order_service.get_items(order.id)
    return order, items[0]


async def _setup_warehouse(session, org_id, user_id, country="US", state="NY", is_default=False):
    warehouse_service = WarehouseService(session, organization_id=org_id)
    return await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Main", code=f"MAIN-{country}-{state}", country=country, state=state, is_default=is_default), created_by=user_id)


def test_create_shipment_allocates_matching_warehouse(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order, order_item = await _setup_order(app_session, user.organization_id, user.id, quantity=3)
        far_warehouse = await _setup_warehouse(app_session, user.organization_id, user.id, country="US", state="CA")
        near_warehouse = await _setup_warehouse(app_session, user.organization_id, user.id, country="US", state="NY")

        service = ShipmentService(app_session, organization_id=user.organization_id)
        shipment = await service.create_shipment(ShipmentCreateRequest(
            order_id=order.id, items=[ShipmentItemInput(order_item_id=order_item.id, quantity=2)],
        ), created_by=user.id)

        assert shipment.warehouse_id == near_warehouse.id
        assert shipment.shipment_number.startswith("SHP-")
        assert shipment.status.value == "pending"

    asyncio.run(_run())


def test_create_shipment_rejects_over_allocation(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order, order_item = await _setup_order(app_session, user.organization_id, user.id, quantity=2)
        await _setup_warehouse(app_session, user.organization_id, user.id, is_default=True)

        service = ShipmentService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await service.create_shipment(ShipmentCreateRequest(
                order_id=order.id, items=[ShipmentItemInput(order_item_id=order_item.id, quantity=5)],
            ), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_split_shipment_across_two_calls(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order, order_item = await _setup_order(app_session, user.organization_id, user.id, quantity=4)
        await _setup_warehouse(app_session, user.organization_id, user.id, is_default=True)

        service = ShipmentService(app_session, organization_id=user.organization_id)
        first = await service.create_shipment(ShipmentCreateRequest(
            order_id=order.id, items=[ShipmentItemInput(order_item_id=order_item.id, quantity=2)],
        ), created_by=user.id)
        second = await service.create_shipment(ShipmentCreateRequest(
            order_id=order.id, items=[ShipmentItemInput(order_item_id=order_item.id, quantity=2)],
        ), created_by=user.id)

        assert first.id != second.id

        with pytest.raises(HTTPException) as exc_info:
            await service.create_shipment(ShipmentCreateRequest(
                order_id=order.id, items=[ShipmentItemInput(order_item_id=order_item.id, quantity=1)],
            ), created_by=user.id)
        assert exc_info.value.status_code == 400

        from app.repositories.order_repository import OrderItemRepository
        item_repo = OrderItemRepository(app_session, organization_id=user.organization_id)
        refreshed_item = await item_repo.get_by_id(order_item.id)
        assert refreshed_item.quantity_fulfilled == 4

    asyncio.run(_run())


def test_default_provider_selected_when_not_specified(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order, order_item = await _setup_order(app_session, user.organization_id, user.id, quantity=2)
        await _setup_warehouse(app_session, user.organization_id, user.id, is_default=True)

        provider_service = ShippingProviderService(app_session, organization_id=user.organization_id)
        provider = await provider_service.create_provider(ShippingProviderCreateRequest(
            name="Shiprocket", code="shiprocket", is_default=True, base_rate=15.0,
        ), created_by=user.id)

        service = ShipmentService(app_session, organization_id=user.organization_id)
        shipment = await service.create_shipment(ShipmentCreateRequest(
            order_id=order.id, items=[ShipmentItemInput(order_item_id=order_item.id, quantity=2)],
        ), created_by=user.id)

        assert shipment.shipping_provider_id == provider.id
        assert shipment.shipping_cost == 15.0
        assert shipment.carrier_name == "Shiprocket"

    asyncio.run(_run())


def test_full_shipment_lifecycle(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order, order_item = await _setup_order(app_session, user.organization_id, user.id, quantity=1)
        await _setup_warehouse(app_session, user.organization_id, user.id, is_default=True)

        service = ShipmentService(app_session, organization_id=user.organization_id)
        shipment = await service.create_shipment(ShipmentCreateRequest(
            order_id=order.id, items=[ShipmentItemInput(order_item_id=order_item.id, quantity=1)],
        ), created_by=user.id)

        shipment = await service.generate_label(shipment.id)
        assert shipment.status.value == "label_generated"
        assert shipment.tracking_number is not None

        shipment = await service.mark_picked_up(shipment.id)
        shipment = await service.mark_in_transit(shipment.id)
        shipment = await service.mark_out_for_delivery(shipment.id)
        shipment = await service.mark_delivered(shipment.id)

        assert shipment.status.value == "delivered"
        assert shipment.delivered_at is not None

    asyncio.run(_run())


def test_cancel_shipment_reverts_fulfilled_quantity(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order, order_item = await _setup_order(app_session, user.organization_id, user.id, quantity=2)
        await _setup_warehouse(app_session, user.organization_id, user.id, is_default=True)

        service = ShipmentService(app_session, organization_id=user.organization_id)
        shipment = await service.create_shipment(ShipmentCreateRequest(
            order_id=order.id, items=[ShipmentItemInput(order_item_id=order_item.id, quantity=2)],
        ), created_by=user.id)

        from app.repositories.order_repository import OrderItemRepository
        item_repo = OrderItemRepository(app_session, organization_id=user.organization_id)
        before = await item_repo.get_by_id(order_item.id)
        assert before.quantity_fulfilled == 2

        cancelled = await service.cancel_shipment(shipment.id, reason="Customer requested change")
        assert cancelled.status.value == "cancelled"

        await app_session.refresh(before)
        assert before.quantity_fulfilled == 0

    asyncio.run(_run())


def test_invalid_transition_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order, order_item = await _setup_order(app_session, user.organization_id, user.id, quantity=1)
        await _setup_warehouse(app_session, user.organization_id, user.id, is_default=True)

        service = ShipmentService(app_session, organization_id=user.organization_id)
        shipment = await service.create_shipment(ShipmentCreateRequest(
            order_id=order.id, items=[ShipmentItemInput(order_item_id=order_item.id, quantity=1)],
        ), created_by=user.id)

        with pytest.raises(HTTPException) as exc_info:
            await service.mark_delivered(shipment.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        order, order_item = await _setup_order(app_session, user_a.organization_id, user_a.id, quantity=1)
        await _setup_warehouse(app_session, user_a.organization_id, user_a.id, is_default=True)

        service_a = ShipmentService(app_session, organization_id=user_a.organization_id)
        service_b = ShipmentService(app_session, organization_id=user_b.organization_id)
        shipment = await service_a.create_shipment(ShipmentCreateRequest(
            order_id=order.id, items=[ShipmentItemInput(order_item_id=order_item.id, quantity=1)],
        ), created_by=user_a.id)

        assert await service_b.get_shipment(shipment.id) is None

    asyncio.run(_run())

