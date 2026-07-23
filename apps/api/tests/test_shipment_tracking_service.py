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
from app.schemas.shipment_tracking import ShipmentTrackingEventCreateRequest, ShipmentTrackingWebhookRequest
from app.schemas.shipping_provider import ShippingProviderCreateRequest
from app.schemas.warehouse import WarehouseCreateRequest
from app.services.auth_service import AuthService
from app.services.customer_service import CustomerService
from app.services.order_service import OrderService
from app.services.pricing_service import PricingService
from app.services.product_service import ProductService
from app.services.shipment_service import ShipmentService
from app.services.shipment_tracking_service import ShipmentTrackingService
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
    return OrderAddressInput(first_name="Ada", last_name="Lovelace", line1="1 Main St", city="Metropolis", country="US")


async def _register_org(session, email="owner@example.com", org_name="Tracking Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _setup_shipment(session, org_id, user_id, provider_code="manual-carrier", webhook_secret=None):
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
    items = await order_service.get_items(order.id)

    warehouse_service = WarehouseService(session, organization_id=org_id)
    await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Main", code="MAIN"), created_by=user_id)

    provider_service = ShippingProviderService(session, organization_id=org_id)
    await provider_service.create_provider(ShippingProviderCreateRequest(name="Manual Carrier", code=provider_code, webhook_secret=webhook_secret), created_by=user_id)

    shipment_service = ShipmentService(session, organization_id=org_id)
    shipment = await shipment_service.create_shipment(ShipmentCreateRequest(
        order_id=order.id, items=[ShipmentItemInput(order_item_id=items[0].id, quantity=1)],
    ), created_by=user_id)
    shipment = await shipment_service.generate_label(shipment.id)
    return shipment


def test_add_manual_tracking_event(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        shipment = await _setup_shipment(app_session, user.organization_id, user.id)

        service = ShipmentTrackingService(app_session, organization_id=user.organization_id)
        event = await service.add_event(shipment.id, ShipmentTrackingEventCreateRequest(status="picked_up", description="Courier collected the package"))

        assert event.status == "picked_up"
        timeline = await service.get_timeline(shipment.id)
        assert len(timeline) == 1

        from app.services.shipment_service import ShipmentService as SS
        shipment_service = SS(app_session, organization_id=user.organization_id)
        refreshed = await shipment_service.get_shipment(shipment.id)
        assert refreshed.status.value == "picked_up"

    asyncio.run(_run())


def test_webhook_updates_shipment_status(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        shipment = await _setup_shipment(app_session, user.organization_id, user.id, provider_code="webhook-carrier")

        service = ShipmentTrackingService(app_session, organization_id=user.organization_id)
        # Shipment starts at "label_generated"; "picked_up" is the valid next
        # step in the state machine, so this webhook should apply cleanly.
        await service.process_webhook(ShipmentTrackingWebhookRequest(
            provider_code="webhook-carrier", tracking_number=shipment.tracking_number, status="picked_up", description="Courier collected the package",
        ))

        from app.services.shipment_service import ShipmentService as SS
        shipment_service = SS(app_session, organization_id=user.organization_id)
        refreshed = await shipment_service.get_shipment(shipment.id)
        assert refreshed.status.value == "picked_up"

    asyncio.run(_run())


def test_webhook_rejects_wrong_secret(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        shipment = await _setup_shipment(app_session, user.organization_id, user.id, provider_code="secured-carrier", webhook_secret="correct-secret")

        service = ShipmentTrackingService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await service.process_webhook(ShipmentTrackingWebhookRequest(
                provider_code="secured-carrier", tracking_number=shipment.tracking_number, status="in_transit",
            ), webhook_secret="wrong-secret")
        assert exc_info.value.status_code == 401

    asyncio.run(_run())


def test_webhook_accepts_correct_secret(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        shipment = await _setup_shipment(app_session, user.organization_id, user.id, provider_code="secured-carrier-2", webhook_secret="correct-secret")

        service = ShipmentTrackingService(app_session, organization_id=user.organization_id)
        event = await service.process_webhook(ShipmentTrackingWebhookRequest(
            provider_code="secured-carrier-2", tracking_number=shipment.tracking_number, status="delivered",
        ), webhook_secret="correct-secret")
        assert event.status == "delivered"

    asyncio.run(_run())


def test_webhook_unknown_tracking_number_404(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        await _setup_shipment(app_session, user.organization_id, user.id, provider_code="carrier-x")

        service = ShipmentTrackingService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await service.process_webhook(ShipmentTrackingWebhookRequest(
                provider_code="carrier-x", tracking_number="NONEXISTENT", status="delivered",
            ))
        assert exc_info.value.status_code == 404

    asyncio.run(_run())


def test_invalid_status_transition_does_not_crash_webhook(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        shipment = await _setup_shipment(app_session, user.organization_id, user.id, provider_code="carrier-y")

        service = ShipmentTrackingService(app_session, organization_id=user.organization_id)
        # "delivered" from label_generated status is not a valid direct
        # transition; the tracking event should still be recorded.
        event = await service.process_webhook(ShipmentTrackingWebhookRequest(
            provider_code="carrier-y", tracking_number=shipment.tracking_number, status="delivered",
        ))
        assert event.status == "delivered"
        timeline = await service.get_timeline(shipment.id)
        assert len(timeline) == 1

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        shipment = await _setup_shipment(app_session, user_a.organization_id, user_a.id)

        service_a = ShipmentTrackingService(app_session, organization_id=user_a.organization_id)
        service_b = ShipmentTrackingService(app_session, organization_id=user_b.organization_id)
        await service_a.add_event(shipment.id, ShipmentTrackingEventCreateRequest(status="picked_up"))

        timeline_b = await service_b.get_timeline(shipment.id)
        assert timeline_b == []

    asyncio.run(_run())

