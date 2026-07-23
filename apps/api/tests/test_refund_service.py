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
from app.schemas.refund import RefundCreateRequest, RefundMethod
from app.services.auth_service import AuthService
from app.services.customer_service import CustomerService
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.services.pricing_service import PricingService
from app.services.product_service import ProductService
from app.services.refund_service import RefundService


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


async def _register_org(session, email="owner@example.com", org_name="Refund Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _setup_paid_order(session, org_id, user_id, price=100.0, quantity=1) -> tuple[str, str]:
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

    payment_service = PaymentService(session, organization_id=org_id)
    await payment_service.create_payment_attempt(order.id, PaymentAttemptCreateRequest(method="card", amount=order.total), created_by=user_id)

    return order.id, customer.id


def test_create_refund_request_rejects_over_refundable_amount(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order_id, customer_id = await _setup_paid_order(app_session, user.organization_id, user.id, price=100.0)

        refund_service = RefundService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await refund_service.create_refund_request(RefundCreateRequest(order_id=order_id, amount=500.0), requested_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_full_refund_approval_workflow(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order_id, customer_id = await _setup_paid_order(app_session, user.organization_id, user.id, price=100.0)

        refund_service = RefundService(app_session, organization_id=user.organization_id)
        refund = await refund_service.create_refund_request(RefundCreateRequest(
            order_id=order_id, method=RefundMethod.original_payment, amount=40.0, reason="Customer request",
        ), requested_by=user.id)
        assert refund.status.value == "requested"
        assert refund.refund_number.startswith("REF-")

        approved = await refund_service.approve_refund(refund.id, changed_by=user.id)
        assert approved.status.value == "approved"
        assert approved.approved_by == user.id

        completed = await refund_service.complete_refund(refund.id, changed_by=user.id)
        assert completed.status.value == "completed"
        assert completed.payment_attempt_id is not None
        assert completed.processed_at is not None

        order = await refund_service.order_repo.get_by_id(order_id)
        assert order.amount_refunded == 40.0
        assert order.payment_status.value == "partially_refunded"

    asyncio.run(_run())


def test_cannot_over_refund_across_multiple_pending_requests(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order_id, customer_id = await _setup_paid_order(app_session, user.organization_id, user.id, price=100.0)

        refund_service = RefundService(app_session, organization_id=user.organization_id)
        await refund_service.create_refund_request(RefundCreateRequest(order_id=order_id, amount=60.0), requested_by=user.id)

        with pytest.raises(HTTPException) as exc_info:
            await refund_service.create_refund_request(RefundCreateRequest(order_id=order_id, amount=60.0), requested_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_reject_refund_then_cannot_complete(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order_id, customer_id = await _setup_paid_order(app_session, user.organization_id, user.id, price=100.0)

        refund_service = RefundService(app_session, organization_id=user.organization_id)
        refund = await refund_service.create_refund_request(RefundCreateRequest(order_id=order_id, amount=50.0), requested_by=user.id)

        rejected = await refund_service.reject_refund(refund.id, changed_by=user.id, reason="Not eligible")
        assert rejected.status.value == "rejected"

        with pytest.raises(HTTPException) as exc_info:
            await refund_service.complete_refund(refund.id, changed_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_store_credit_refund_still_updates_order_accounting(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order_id, customer_id = await _setup_paid_order(app_session, user.organization_id, user.id, price=100.0)

        refund_service = RefundService(app_session, organization_id=user.organization_id)
        refund = await refund_service.create_refund_request(RefundCreateRequest(
            order_id=order_id, method=RefundMethod.store_credit, amount=25.0,
        ), requested_by=user.id)
        await refund_service.approve_refund(refund.id, changed_by=user.id)
        completed = await refund_service.complete_refund(refund.id, changed_by=user.id)

        assert completed.method.value == "store_credit"
        order = await refund_service.order_repo.get_by_id(order_id)
        assert order.amount_refunded == 25.0

    asyncio.run(_run())


def test_full_refund_marks_order_refunded(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        order_id, customer_id = await _setup_paid_order(app_session, user.organization_id, user.id, price=100.0)

        refund_service = RefundService(app_session, organization_id=user.organization_id)
        refund = await refund_service.create_refund_request(RefundCreateRequest(order_id=order_id, amount=100.0), requested_by=user.id)
        await refund_service.approve_refund(refund.id, changed_by=user.id)
        await refund_service.complete_refund(refund.id, changed_by=user.id)

        order = await refund_service.order_repo.get_by_id(order_id)
        assert order.payment_status.value == "refunded"

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        order_id, customer_id = await _setup_paid_order(app_session, user_a.organization_id, user_a.id)

        refund_service_a = RefundService(app_session, organization_id=user_a.organization_id)
        refund_service_b = RefundService(app_session, organization_id=user_b.organization_id)
        refund = await refund_service_a.create_refund_request(RefundCreateRequest(order_id=order_id, amount=10.0), requested_by=user_a.id)

        assert await refund_service_b.get_refund(refund.id) is None

    asyncio.run(_run())

