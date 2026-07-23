import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.customer import CustomerCreateRequest
from app.schemas.order import OrderAddressInput, OrderCreateRequest, OrderLineItemInput
from app.schemas.product import ProductCreateRequest
from app.schemas.product_price import ProductPriceCreateRequest
from app.schemas.shipment import ShipmentCreateRequest, ShipmentItemInput
from app.schemas.warehouse import WarehouseCreateRequest
from app.services.auth_service import AuthService
from app.services.customer_service import CustomerService
from app.services.order_service import OrderService
from app.services.pricing_service import PricingService
from app.services.product_service import ProductService
from app.services.shipment_service import ShipmentService
from app.services.shipping_label_service import ShippingLabelService
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


async def _register_org(session, email="owner@example.com", org_name="Label Test Org"):
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

    warehouse_service = WarehouseService(session, organization_id=org_id)
    warehouse = await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Main", code=f"MAIN-{suffix}"), created_by=user_id)

    shipment_service = ShipmentService(session, organization_id=org_id)
    shipment = await shipment_service.create_shipment(ShipmentCreateRequest(
        order_id=order.id, items=[ShipmentItemInput(order_item_id=items[0].id, quantity=1)],
    ), created_by=user_id)
    shipment = await shipment_service.generate_label(shipment.id)
    return shipment, warehouse


def test_render_label_html_contains_tracking_number(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        shipment, warehouse = await _setup_shipment(app_session, user.organization_id, user.id)

        service = ShippingLabelService(app_session, organization_id=user.organization_id)
        html = await service.render_label_html(shipment.id, generated_by=user.id)

        assert shipment.tracking_number in html
        assert "Widget" in html

        history = await service.get_history(shipment.id)
        assert len(history) == 1
        assert history[0].label_type.value == "label"

    asyncio.run(_run())


def test_render_packing_slip_omits_pricing(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        shipment, warehouse = await _setup_shipment(app_session, user.organization_id, user.id)

        service = ShippingLabelService(app_session, organization_id=user.organization_id)
        html = await service.render_packing_slip_html(shipment.id, generated_by=user.id)

        assert "Packing Slip" in html
        assert "Widget" in html
        assert "25.0" not in html

    asyncio.run(_run())


def test_render_manifest_lists_multiple_shipments(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        shipment_one, warehouse = await _setup_shipment(app_session, user.organization_id, user.id, suffix="1")
        shipment_two, _ = await _setup_shipment(app_session, user.organization_id, user.id, suffix="2")

        service = ShippingLabelService(app_session, organization_id=user.organization_id)
        html = await service.render_manifest_html(warehouse.id, [shipment_one.id, shipment_two.id], generated_by=user.id)

        assert shipment_one.shipment_number in html
        assert shipment_two.shipment_number in html
        assert "2 shipment(s)" in html

    asyncio.run(_run())


def test_bulk_labels_concatenates_all_shipments(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        shipment_one, _ = await _setup_shipment(app_session, user.organization_id, user.id, suffix="1")
        shipment_two, _ = await _setup_shipment(app_session, user.organization_id, user.id, suffix="2")

        service = ShippingLabelService(app_session, organization_id=user.organization_id)
        html = await service.render_bulk_labels_html([shipment_one.id, shipment_two.id], generated_by=user.id)

        assert shipment_one.tracking_number in html
        assert shipment_two.tracking_number in html

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        from fastapi import HTTPException

        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        shipment, warehouse = await _setup_shipment(app_session, user_a.organization_id, user_a.id)

        service_b = ShippingLabelService(app_session, organization_id=user_b.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await service_b.render_label_html(shipment.id)
        assert exc_info.value.status_code == 404

    asyncio.run(_run())

