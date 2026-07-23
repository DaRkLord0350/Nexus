import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.checkout import CheckoutQuoteRequest, CheckoutRequest
from app.schemas.customer import CustomerCreateRequest
from app.schemas.order import OrderAddressInput
from app.schemas.product import ProductCreateRequest
from app.schemas.product_price import ProductPriceCreateRequest
from app.schemas.tax import TaxClassCreateRequest, TaxRateCreateRequest
from app.schemas.warehouse import WarehouseCreateRequest
from app.services.auth_service import AuthService
from app.services.cart_service import CartService
from app.services.checkout_service import CheckoutService
from app.services.customer_service import CustomerService
from app.services.pricing_service import PricingService
from app.services.product_service import ProductService
from app.services.tax_service import TaxService
from app.services.warehouse_service import WarehouseService
from app.schemas.cart import CartItemAddRequest


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


async def _register_org(session, email="owner@example.com", org_name="Checkout Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _setup_published_product(session, org_id, user_id, price: float = 50.0, tax_class_id=None, sku="WID-1"):
    product_service = ProductService(session, organization_id=org_id)
    product = await product_service.create_product(ProductCreateRequest(name="Widget", sku=sku, tax_class_id=tax_class_id, track_inventory=False), created_by=user_id)
    product = await product_service.publish_product(product.id, actor_id=user_id)

    pricing_service = PricingService(session, organization_id=org_id)
    await pricing_service.create_price(ProductPriceCreateRequest(product_id=product.id, currency="USD", selling_price=price), created_by=user_id)
    return product


async def _setup_default_warehouse(session, org_id, user_id):
    warehouse_service = WarehouseService(session, organization_id=org_id)
    return await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Main", code="MAIN", is_default=True), created_by=user_id)


def test_guest_checkout_creates_order_and_converts_cart(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product = await _setup_published_product(app_session, user.organization_id, user.id, price=50.0)
        await _setup_default_warehouse(app_session, user.organization_id, user.id)

        cart_service = CartService(app_session, organization_id=user.organization_id)
        cart = await cart_service.get_or_create_cart(customer_id=None, session_token="guest-checkout-1")
        await cart_service.add_item(cart.id, CartItemAddRequest(product_id=product.id, quantity=2))

        checkout_service = CheckoutService(app_session, organization_id=user.organization_id)
        order = await checkout_service.checkout(CheckoutRequest(
            cart_id=cart.id, session_token="guest-checkout-1",
            guest_email="guest@example.com", guest_first_name="Gwen", guest_last_name="Guest",
            billing_address=_address(), shipping_address=_address(), payment_method="cod",
        ), current_customer_id=None)

        assert order.subtotal == 100.0
        assert order.shipping_amount == 0.0  # over free-shipping threshold
        assert order.status.value == "pending"

        refreshed_cart = await cart_service.get_cart(cart.id)
        assert refreshed_cart.status.value == "converted"
        assert refreshed_cart.order_id == order.id

    asyncio.run(_run())


def test_checkout_empty_cart_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        cart_service = CartService(app_session, organization_id=user.organization_id)
        cart = await cart_service.get_or_create_cart(customer_id=None, session_token="empty-cart")

        checkout_service = CheckoutService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await checkout_service.checkout(CheckoutRequest(
                cart_id=cart.id, session_token="empty-cart", guest_email="a@example.com",
                guest_first_name="A", guest_last_name="B", billing_address=_address(), shipping_address=_address(),
            ), current_customer_id=None)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_checkout_wrong_session_token_forbidden(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product = await _setup_published_product(app_session, user.organization_id, user.id, price=10.0)
        cart_service = CartService(app_session, organization_id=user.organization_id)
        cart = await cart_service.get_or_create_cart(customer_id=None, session_token="real-token")
        await cart_service.add_item(cart.id, CartItemAddRequest(product_id=product.id, quantity=1))

        checkout_service = CheckoutService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await checkout_service.checkout(CheckoutRequest(
                cart_id=cart.id, session_token="wrong-token", guest_email="a@example.com",
                guest_first_name="A", guest_last_name="B", billing_address=_address(), shipping_address=_address(),
            ), current_customer_id=None)
        assert exc_info.value.status_code == 403

    asyncio.run(_run())


def test_authenticated_checkout_uses_saved_address(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product = await _setup_published_product(app_session, user.organization_id, user.id, price=30.0)
        customer_service = CustomerService(app_session, organization_id=user.organization_id)
        customer = await customer_service.create_customer(CustomerCreateRequest(email="c@example.com", first_name="C", last_name="D"), created_by=user.id)

        from app.schemas.address import AddressCreateRequest
        address = await customer_service.add_address(customer.id, AddressCreateRequest(
            first_name="C", last_name="D", line1="99 Home Ave", city="Gotham", country="us", is_default=True,
        ))

        cart_service = CartService(app_session, organization_id=user.organization_id)
        cart = await cart_service.get_or_create_cart(customer_id=customer.id, session_token=None)
        await cart_service.add_item(cart.id, CartItemAddRequest(product_id=product.id, quantity=1))

        checkout_service = CheckoutService(app_session, organization_id=user.organization_id)
        order = await checkout_service.checkout(CheckoutRequest(
            cart_id=cart.id, billing_address_id=address.id, shipping_address_id=address.id, payment_method="cod",
        ), current_customer_id=customer.id)

        assert order.customer_id == customer.id
        assert order.shipping_city == "Gotham"
        assert order.shipping_line1 == "99 Home Ave"

    asyncio.run(_run())


def test_checkout_applies_tax(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        tax_service = TaxService(app_session, organization_id=user.organization_id)
        tax_class = await tax_service.create_tax_class(TaxClassCreateRequest(name="Standard", code="STD"), created_by=user.id)
        await tax_service.create_tax_rate(tax_class.id, TaxRateCreateRequest(country="US", rate=10))

        product = await _setup_published_product(app_session, user.organization_id, user.id, price=50.0, tax_class_id=tax_class.id)

        cart_service = CartService(app_session, organization_id=user.organization_id)
        cart = await cart_service.get_or_create_cart(customer_id=None, session_token="tax-cart")
        await cart_service.add_item(cart.id, CartItemAddRequest(product_id=product.id, quantity=1))

        checkout_service = CheckoutService(app_session, organization_id=user.organization_id)
        order = await checkout_service.checkout(CheckoutRequest(
            cart_id=cart.id, session_token="tax-cart", guest_email="tax@example.com",
            guest_first_name="Tax", guest_last_name="Payer", billing_address=_address(), shipping_address=_address(),
        ), current_customer_id=None)

        assert order.tax_amount == 5.0
        assert order.total == 65.0  # 50 subtotal + 5 tax + 10 flat shipping (below free threshold)

    asyncio.run(_run())


def test_quote_matches_checkout_totals(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product = await _setup_published_product(app_session, user.organization_id, user.id, price=20.0)

        cart_service = CartService(app_session, organization_id=user.organization_id)
        cart = await cart_service.get_or_create_cart(customer_id=None, session_token="quote-cart")
        await cart_service.add_item(cart.id, CartItemAddRequest(product_id=product.id, quantity=1))

        checkout_service = CheckoutService(app_session, organization_id=user.organization_id)
        quote = await checkout_service.get_quote(CheckoutQuoteRequest(cart_id=cart.id, session_token="quote-cart", country="US"), current_customer_id=None)

        assert quote["subtotal"] == 20.0
        assert quote["shipping_amount"] == 10.0
        assert quote["total"] == 30.0

    asyncio.run(_run())

