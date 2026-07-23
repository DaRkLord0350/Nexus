import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.customer import CustomerCreateRequest
from app.schemas.order import OrderAddressInput, OrderCreateRequest, OrderLineItemInput
from app.schemas.payment import PaymentAttemptCreateRequest
from app.schemas.product import ProductCreateRequest
from app.schemas.product_price import ProductPriceCreateRequest
from app.services.auth_service import AuthService
from app.services.customer_service import CustomerService
from app.services.invoice_service import InvoiceService
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.services.pricing_service import PricingService
from app.services.product_service import ProductService


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


async def _register_org(session, email="owner@example.com", org_name="Payment Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _setup_order(session, org_id, user_id, price=50.0, quantity=2) -> str:
    customer_service = CustomerService(session, organization_id=org_id)
    customer = await customer_service.create_customer(CustomerCreateRequest(email="shopper@example.com", first_name="S", last_name="H"), created_by=user_id)

    product_service = ProductService(session, organization_id=org_id)
    product = await product_service.create_product(ProductCreateRequest(name="Widget", sku="WID-1", track_inventory=False), created_by=user_id)
    product = await product_service.publish_product(product.id, actor_id=user_id)

    pricing_service = PricingService(session, organization_id=org_id)
    await pricing_service.create_price(ProductPriceCreateRequest(product_id=product.id, currency="USD", selling_price=price), created_by=user_id)

    order_service = OrderService(session, organization_id=org_id)
    order = await order_service.create_order(OrderCreateRequest(
        customer_id=customer.id, billing_address=_address(), shipping_address=_address(),
        items=[OrderLineItemInput(product_id=product.id, quantity=quantity)],
    ), created_by=user_id)
    return order.id


def test_cod_payment_authorized_not_captured(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order_id = await _setup_order(app_session, user.organization_id, user.id, price=50.0, quantity=2)

        payment_service = PaymentService(app_session, organization_id=user.organization_id)
        attempt = await payment_service.create_payment_attempt(order_id, PaymentAttemptCreateRequest(method="cod", amount=100.0), created_by=user.id)

        assert attempt.status.value == "authorized"
        order = await payment_service.order_repo.get_by_id(order_id)
        assert order.amount_paid == 0
        assert order.payment_status.value == "pending"

    asyncio.run(_run())


def test_online_payment_captures_and_updates_order(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order_id = await _setup_order(app_session, user.organization_id, user.id, price=50.0, quantity=2)

        payment_service = PaymentService(app_session, organization_id=user.organization_id)
        attempt = await payment_service.create_payment_attempt(order_id, PaymentAttemptCreateRequest(method="card", amount=100.0), created_by=user.id)

        assert attempt.status.value == "captured"
        assert attempt.gateway_reference is not None
        order = await payment_service.order_repo.get_by_id(order_id)
        assert order.amount_paid == 100.0
        assert order.payment_status.value == "paid"

    asyncio.run(_run())


def test_partial_payment_marks_partially_paid(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order_id = await _setup_order(app_session, user.organization_id, user.id, price=100.0, quantity=1)

        payment_service = PaymentService(app_session, organization_id=user.organization_id)
        await payment_service.create_payment_attempt(order_id, PaymentAttemptCreateRequest(method="card", amount=40.0), created_by=user.id)

        order = await payment_service.order_repo.get_by_id(order_id)
        assert order.amount_paid == 40.0
        assert order.payment_status.value == "partially_paid"

    asyncio.run(_run())


def test_idempotency_key_prevents_double_charge(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order_id = await _setup_order(app_session, user.organization_id, user.id, price=100.0, quantity=1)

        payment_service = PaymentService(app_session, organization_id=user.organization_id)
        first = await payment_service.create_payment_attempt(order_id, PaymentAttemptCreateRequest(method="card", amount=100.0, idempotency_key="idem-1"), created_by=user.id)
        second = await payment_service.create_payment_attempt(order_id, PaymentAttemptCreateRequest(method="card", amount=100.0, idempotency_key="idem-1"), created_by=user.id)

        assert first.id == second.id
        order = await payment_service.order_repo.get_by_id(order_id)
        assert order.amount_paid == 100.0  # only charged once

    asyncio.run(_run())


def test_refund_payment_updates_order(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order_id = await _setup_order(app_session, user.organization_id, user.id, price=100.0, quantity=1)

        payment_service = PaymentService(app_session, organization_id=user.organization_id)
        await payment_service.create_payment_attempt(order_id, PaymentAttemptCreateRequest(method="card", amount=100.0), created_by=user.id)

        refund = await payment_service.refund_payment(order_id, amount=30.0, reason="Partial return", created_by=user.id)
        assert refund.amount == -30.0

        order = await payment_service.order_repo.get_by_id(order_id)
        assert order.amount_refunded == 30.0
        assert order.payment_status.value == "partially_refunded"

        with pytest.raises(HTTPException) as exc_info:
            await payment_service.refund_payment(order_id, amount=1000.0, created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_generate_invoice_is_idempotent(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order_id = await _setup_order(app_session, user.organization_id, user.id, price=50.0, quantity=2)

        invoice_service = InvoiceService(app_session, organization_id=user.organization_id)
        invoice = await invoice_service.generate_invoice(order_id, created_by=user.id)
        assert invoice.invoice_number.startswith("INV-")
        assert invoice.total == 100.0
        assert invoice.amount_due == 100.0

        again = await invoice_service.generate_invoice(order_id, created_by=user.id)
        assert again.id == invoice.id

    asyncio.run(_run())


def test_invoice_syncs_after_payment(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order_id = await _setup_order(app_session, user.organization_id, user.id, price=100.0, quantity=1)

        invoice_service = InvoiceService(app_session, organization_id=user.organization_id)
        invoice = await invoice_service.generate_invoice(order_id, created_by=user.id)

        payment_service = PaymentService(app_session, organization_id=user.organization_id)
        await payment_service.create_payment_attempt(order_id, PaymentAttemptCreateRequest(method="card", amount=100.0), created_by=user.id)

        synced = await invoice_service.sync_with_order(invoice.id)
        assert synced.amount_paid == 100.0
        assert synced.amount_due == 0.0
        assert synced.status.value == "paid"

    asyncio.run(_run())


def test_void_invoice(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order_id = await _setup_order(app_session, user.organization_id, user.id)

        invoice_service = InvoiceService(app_session, organization_id=user.organization_id)
        invoice = await invoice_service.generate_invoice(order_id, created_by=user.id)

        voided = await invoice_service.void_invoice(invoice.id, reason="Duplicate order")
        assert voided.status.value == "void"
        assert voided.void_reason == "Duplicate order"

        with pytest.raises(HTTPException) as exc_info:
            await invoice_service.void_invoice(invoice.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_render_html_contains_invoice_number(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order_id = await _setup_order(app_session, user.organization_id, user.id)

        invoice_service = InvoiceService(app_session, organization_id=user.organization_id)
        invoice = await invoice_service.generate_invoice(order_id, created_by=user.id)

        html = await invoice_service.render_html(invoice.id)
        assert invoice.invoice_number in html
        assert "Widget" in html

    asyncio.run(_run())


def test_cannot_invoice_cancelled_order(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order_id = await _setup_order(app_session, user.organization_id, user.id)

        order_service = OrderService(app_session, organization_id=user.organization_id)
        await order_service.cancel_order(order_id, changed_by=user.id)

        invoice_service = InvoiceService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await invoice_service.generate_invoice(order_id, created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        order_id = await _setup_order(app_session, user_a.organization_id, user_a.id)

        invoice_service_a = InvoiceService(app_session, organization_id=user_a.organization_id)
        invoice_service_b = InvoiceService(app_session, organization_id=user_b.organization_id)
        invoice = await invoice_service_a.generate_invoice(order_id, created_by=user_a.id)

        assert await invoice_service_b.get_invoice(invoice.id) is None

    asyncio.run(_run())

