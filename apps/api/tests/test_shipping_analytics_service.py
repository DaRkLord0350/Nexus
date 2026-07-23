import asyncio

import pytest
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
from app.services.shipping_analytics_service import ShippingAnalyticsService
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


async def _register_org(session, email="owner@example.com", org_name="Analytics Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _create_shipment(session, org_id, user_id, provider_id, warehouse_id, suffix, cod=False, cost=10.0):
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

    shipment_service = ShipmentService(session, organization_id=org_id)
    shipment = await shipment_service.create_shipment(ShipmentCreateRequest(
        order_id=order.id, warehouse_id=warehouse_id, shipping_provider_id=provider_id,
        items=[ShipmentItemInput(order_item_id=items[0].id, quantity=1)],
        is_cod=cod, shipping_cost=cost,
    ), created_by=user_id)
    return shipment, shipment_service


def test_courier_performance_computes_rates(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        warehouse_service = WarehouseService(app_session, organization_id=user.organization_id)
        warehouse = await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Main", code="MAIN"), created_by=user.id)

        provider_service = ShippingProviderService(app_session, organization_id=user.organization_id)
        provider = await provider_service.create_provider(ShippingProviderCreateRequest(name="Delhivery", code="delhivery", base_transit_days=3), created_by=user.id)

        shipment1, shipment_service = await _create_shipment(app_session, user.organization_id, user.id, provider.id, warehouse.id, "1", cod=True, cost=10.0)
        await shipment_service.generate_label(shipment1.id)
        await shipment_service.mark_picked_up(shipment1.id)
        await shipment_service.mark_in_transit(shipment1.id)
        await shipment_service.mark_out_for_delivery(shipment1.id)
        await shipment_service.mark_delivered(shipment1.id)

        shipment2, _ = await _create_shipment(app_session, user.organization_id, user.id, provider.id, warehouse.id, "2", cod=False, cost=20.0)
        await shipment_service.generate_label(shipment2.id)
        await shipment_service.mark_picked_up(shipment2.id)
        await shipment_service.mark_in_transit(shipment2.id)
        await shipment_service.mark_out_for_delivery(shipment2.id)
        await shipment_service.mark_failed_delivery(shipment2.id, reason="Address not found")

        analytics_service = ShippingAnalyticsService(app_session, organization_id=user.organization_id)
        report = await analytics_service.get_courier_performance()

        assert report["summary"]["total_shipments"] == 2
        assert report["summary"]["delivered_count"] == 1
        assert report["summary"]["failed_delivery_count"] == 1
        assert report["summary"]["cod_count"] == 1
        assert report["summary"]["total_shipping_cost"] == 30.0

        assert len(report["providers"]) == 1
        provider_stats = report["providers"][0]
        assert provider_stats["total_shipments"] == 2
        assert provider_stats["delivered_rate"] == 50.0
        assert provider_stats["failed_delivery_rate"] == 50.0
        assert provider_stats["cod_rate"] == 50.0

    asyncio.run(_run())


def test_courier_performance_empty_when_no_shipments(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        analytics_service = ShippingAnalyticsService(app_session, organization_id=user.organization_id)
        report = await analytics_service.get_courier_performance()

        assert report["summary"]["total_shipments"] == 0
        assert report["summary"]["delivered_rate"] == 0
        assert report["providers"] == []

    asyncio.run(_run())


def test_courier_performance_date_filtering(app_session: AsyncSession):
    async def _run():
        from datetime import datetime, timedelta

        user = await _register_org(app_session)
        warehouse_service = WarehouseService(app_session, organization_id=user.organization_id)
        warehouse = await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Main", code="MAIN"), created_by=user.id)
        provider_service = ShippingProviderService(app_session, organization_id=user.organization_id)
        provider = await provider_service.create_provider(ShippingProviderCreateRequest(name="Delhivery", code="delhivery"), created_by=user.id)

        await _create_shipment(app_session, user.organization_id, user.id, provider.id, warehouse.id, "1")

        analytics_service = ShippingAnalyticsService(app_session, organization_id=user.organization_id)
        future_only = await analytics_service.get_courier_performance(date_from=datetime.utcnow() + timedelta(days=1))
        assert future_only["summary"]["total_shipments"] == 0

        all_time = await analytics_service.get_courier_performance(date_from=datetime.utcnow() - timedelta(days=1))
        assert all_time["summary"]["total_shipments"] == 1

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")

        warehouse_service = WarehouseService(app_session, organization_id=user_a.organization_id)
        warehouse = await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Main", code="MAIN"), created_by=user_a.id)
        provider_service = ShippingProviderService(app_session, organization_id=user_a.organization_id)
        provider = await provider_service.create_provider(ShippingProviderCreateRequest(name="Delhivery", code="delhivery"), created_by=user_a.id)
        await _create_shipment(app_session, user_a.organization_id, user_a.id, provider.id, warehouse.id, "1")

        analytics_service_b = ShippingAnalyticsService(app_session, organization_id=user_b.organization_id)
        report_b = await analytics_service_b.get_courier_performance()
        assert report_b["summary"]["total_shipments"] == 0

    asyncio.run(_run())

