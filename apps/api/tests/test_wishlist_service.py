import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.customer import CustomerCreateRequest
from app.schemas.product import ProductCreateRequest
from app.schemas.product_price import ProductPriceCreateRequest
from app.schemas.wishlist import WishlistItemCreateRequest
from app.services.auth_service import AuthService
from app.services.customer_service import CustomerService
from app.services.pricing_service import PricingService
from app.services.product_service import ProductService
from app.services.wishlist_service import WishlistService


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


async def _register_org(session, email="owner@example.com", org_name="Wishlist Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _setup_customer_and_product(session, org_id, user_id, price=20.0, track_inventory=False):
    customer_service = CustomerService(session, organization_id=org_id)
    customer = await customer_service.create_customer(CustomerCreateRequest(email="shopper@example.com", first_name="S", last_name="H"), created_by=user_id)

    product_service = ProductService(session, organization_id=org_id)
    product = await product_service.create_product(ProductCreateRequest(name="Widget", sku="WID-1", track_inventory=track_inventory), created_by=user_id)
    product = await product_service.publish_product(product.id, actor_id=user_id)

    pricing_service = PricingService(session, organization_id=org_id)
    await pricing_service.create_price(ProductPriceCreateRequest(product_id=product.id, currency="USD", selling_price=price), created_by=user_id)
    return customer, product


def test_add_item_is_idempotent(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        customer, product = await _setup_customer_and_product(app_session, user.organization_id, user.id)

        service = WishlistService(app_session, organization_id=user.organization_id)
        first = await service.add_item(customer.id, WishlistItemCreateRequest(product_id=product.id))
        second = await service.add_item(customer.id, WishlistItemCreateRequest(product_id=product.id))

        assert first.id == second.id
        items, total = await service.list_items(customer.id)
        assert total == 1

    asyncio.run(_run())


def test_add_item_missing_product_404(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        customer_service = CustomerService(app_session, organization_id=user.organization_id)
        customer = await customer_service.create_customer(CustomerCreateRequest(email="c@example.com", first_name="C", last_name="D"), created_by=user.id)

        service = WishlistService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await service.add_item(customer.id, WishlistItemCreateRequest(product_id="nonexistent"))
        assert exc_info.value.status_code == 404

    asyncio.run(_run())


def test_remove_item(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        customer, product = await _setup_customer_and_product(app_session, user.organization_id, user.id)

        service = WishlistService(app_session, organization_id=user.organization_id)
        item = await service.add_item(customer.id, WishlistItemCreateRequest(product_id=product.id))
        await service.remove_item(customer.id, item.id)

        items, total = await service.list_items(customer.id)
        assert total == 0

    asyncio.run(_run())


def test_cannot_remove_other_customers_item(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        customer, product = await _setup_customer_and_product(app_session, user.organization_id, user.id)

        customer_service = CustomerService(app_session, organization_id=user.organization_id)
        other = await customer_service.create_customer(CustomerCreateRequest(email="other@example.com", first_name="O", last_name="P"), created_by=user.id)

        service = WishlistService(app_session, organization_id=user.organization_id)
        item = await service.add_item(customer.id, WishlistItemCreateRequest(product_id=product.id))

        with pytest.raises(HTTPException) as exc_info:
            await service.remove_item(other.id, item.id)
        assert exc_info.value.status_code == 404

    asyncio.run(_run())


def test_move_to_cart_creates_cart_item_and_removes_wishlist_entry(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        customer, product = await _setup_customer_and_product(app_session, user.organization_id, user.id, price=15.0)

        service = WishlistService(app_session, organization_id=user.organization_id)
        item = await service.add_item(customer.id, WishlistItemCreateRequest(product_id=product.id))

        cart_item = await service.move_to_cart(customer.id, item.id, quantity=2)
        assert cart_item.quantity == 2
        assert cart_item.unit_price == 15.0

        items, total = await service.list_items(customer.id)
        assert total == 0

        cart = await service.cart_service.get_or_create_cart(customer_id=customer.id, session_token=None)
        cart_items = await service.cart_service.item_repo.list_for_cart(cart.id)
        assert len(cart_items) == 1

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        customer, product = await _setup_customer_and_product(app_session, user_a.organization_id, user_a.id)

        service_a = WishlistService(app_session, organization_id=user_a.organization_id)
        service_b = WishlistService(app_session, organization_id=user_b.organization_id)
        item = await service_a.add_item(customer.id, WishlistItemCreateRequest(product_id=product.id))

        assert await service_b.repo.get_by_id(item.id) is None

    asyncio.run(_run())

