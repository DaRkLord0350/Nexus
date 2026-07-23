import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.cart import CartCouponRequest, CartItemAddRequest, CartItemUpdateRequest
from app.schemas.coupon import CouponCreateRequest, CouponDiscountType
from app.schemas.customer import CustomerCreateRequest
from app.schemas.product import ProductCreateRequest
from app.schemas.product_price import ProductPriceCreateRequest
from app.services.auth_service import AuthService
from app.services.cart_service import CartService
from app.services.coupon_service import CouponService
from app.services.customer_service import CustomerService
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


async def _register_org(session, email="owner@example.com", org_name="Cart Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _setup_published_product(session, org_id, user_id, price: float = 25.0, track_inventory: bool = False):
    product_service = ProductService(session, organization_id=org_id)
    product = await product_service.create_product(ProductCreateRequest(name="Widget", sku=f"WID-{price}", track_inventory=track_inventory), created_by=user_id)
    product = await product_service.publish_product(product.id, actor_id=user_id)

    pricing_service = PricingService(session, organization_id=org_id)
    await pricing_service.create_price(ProductPriceCreateRequest(product_id=product.id, currency="USD", selling_price=price), created_by=user_id)
    return product


async def _setup_customer(session, org_id, user_id):
    customer_service = CustomerService(session, organization_id=org_id)
    return await customer_service.create_customer(CustomerCreateRequest(email="shopper@example.com", first_name="S", last_name="H"), created_by=user_id)


def test_guest_cart_add_item_computes_totals(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product = await _setup_published_product(app_session, user.organization_id, user.id, price=25.0)
        service = CartService(app_session, organization_id=user.organization_id)

        cart = await service.get_or_create_cart(customer_id=None, session_token="guest-token-1")
        item = await service.add_item(cart.id, CartItemAddRequest(product_id=product.id, quantity=2))
        assert item.unit_price == 25.0

        refreshed = await service.get_cart(cart.id)
        assert refreshed.subtotal == 50.0
        assert refreshed.total == 50.0

    asyncio.run(_run())


def test_adding_same_product_merges_quantity(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product = await _setup_published_product(app_session, user.organization_id, user.id)
        service = CartService(app_session, organization_id=user.organization_id)
        cart = await service.get_or_create_cart(customer_id=None, session_token="guest-token-2")

        await service.add_item(cart.id, CartItemAddRequest(product_id=product.id, quantity=1))
        item = await service.add_item(cart.id, CartItemAddRequest(product_id=product.id, quantity=3))

        items = await service.item_repo.list_for_cart(cart.id)
        assert len(items) == 1
        assert item.quantity == 4

    asyncio.run(_run())


def test_unpublished_product_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product_service = ProductService(app_session, organization_id=user.organization_id)
        product = await product_service.create_product(ProductCreateRequest(name="Draft Widget", sku="DRAFT-1"), created_by=user.id)

        service = CartService(app_session, organization_id=user.organization_id)
        cart = await service.get_or_create_cart(customer_id=None, session_token="guest-token-3")

        with pytest.raises(HTTPException) as exc_info:
            await service.add_item(cart.id, CartItemAddRequest(product_id=product.id, quantity=1))
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_stock_limit_enforced_without_backorders(app_session: AsyncSession):
    async def _run():
        from app.schemas.warehouse import WarehouseCreateRequest
        from app.services.stock_movement_service import StockMovementService
        from app.services.warehouse_service import WarehouseService
        from app.models.inventory_transaction import InventoryTransactionType

        user = await _register_org(app_session)
        product = await _setup_published_product(app_session, user.organization_id, user.id, track_inventory=True)
        warehouse_service = WarehouseService(app_session, organization_id=user.organization_id)
        warehouse = await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Main", code="MAIN"), created_by=user.id)

        stock_service = StockMovementService(app_session, organization_id=user.organization_id)
        await stock_service.apply_movement(
            product_id=product.id, variant_id=None, warehouse_id=warehouse.id,
            transaction_type=InventoryTransactionType.adjustment, quantity_delta=5, field="quantity_available",
        )

        service = CartService(app_session, organization_id=user.organization_id)
        cart = await service.get_or_create_cart(customer_id=None, session_token="guest-token-4")

        await service.add_item(cart.id, CartItemAddRequest(product_id=product.id, quantity=5))
        with pytest.raises(HTTPException) as exc_info:
            await service.add_item(cart.id, CartItemAddRequest(product_id=product.id, quantity=1))
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_apply_and_remove_coupon(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product = await _setup_published_product(app_session, user.organization_id, user.id, price=100.0)
        coupon_service = CouponService(app_session, organization_id=user.organization_id)
        await coupon_service.create_coupon(CouponCreateRequest(code="SAVE10", discount_type=CouponDiscountType.percentage, discount_value=10), created_by=user.id)

        service = CartService(app_session, organization_id=user.organization_id)
        cart = await service.get_or_create_cart(customer_id=None, session_token="guest-token-5")
        await service.add_item(cart.id, CartItemAddRequest(product_id=product.id, quantity=1))

        applied = await service.apply_coupon(cart.id, "SAVE10")
        assert applied.discount_amount == 10.0
        assert applied.total == 90.0

        removed = await service.remove_coupon(cart.id)
        assert removed.discount_amount == 0
        assert removed.total == 100.0

    asyncio.run(_run())


def test_remove_item_recomputes_totals(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product = await _setup_published_product(app_session, user.organization_id, user.id, price=10.0)
        service = CartService(app_session, organization_id=user.organization_id)
        cart = await service.get_or_create_cart(customer_id=None, session_token="guest-token-6")
        item = await service.add_item(cart.id, CartItemAddRequest(product_id=product.id, quantity=2))

        await service.remove_item(cart.id, item.id)
        refreshed = await service.get_cart(cart.id)
        assert refreshed.subtotal == 0
        assert refreshed.total == 0

    asyncio.run(_run())


def test_update_item_saved_for_later_excluded_from_totals(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product = await _setup_published_product(app_session, user.organization_id, user.id, price=10.0)
        service = CartService(app_session, organization_id=user.organization_id)
        cart = await service.get_or_create_cart(customer_id=None, session_token="guest-token-7")
        item = await service.add_item(cart.id, CartItemAddRequest(product_id=product.id, quantity=2))

        await service.update_item(cart.id, item.id, CartItemUpdateRequest(saved_for_later=True))
        refreshed = await service.get_cart(cart.id)
        assert refreshed.subtotal == 0

    asyncio.run(_run())


def test_merge_guest_cart_into_customer_cart(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product = await _setup_published_product(app_session, user.organization_id, user.id, price=10.0)
        customer = await _setup_customer(app_session, user.organization_id, user.id)
        service = CartService(app_session, organization_id=user.organization_id)

        guest_cart = await service.get_or_create_cart(customer_id=None, session_token="guest-token-8")
        await service.add_item(guest_cart.id, CartItemAddRequest(product_id=product.id, quantity=3))

        merged = await service.merge_guest_cart(customer.id, "guest-token-8")
        assert merged.customer_id == customer.id
        assert merged.subtotal == 30.0

        stale_guest = await service.get_cart(guest_cart.id)
        assert stale_guest.status.value == "merged"

    asyncio.run(_run())


def test_cart_access_control(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CartService(app_session, organization_id=user.organization_id)
        cart = await service.get_or_create_cart(customer_id=None, session_token="guest-token-9")

        with pytest.raises(HTTPException) as exc_info:
            service.assert_access(cart, None, "wrong-token")
        assert exc_info.value.status_code == 403

        service.assert_access(cart, None, "guest-token-9")

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")

        service_a = CartService(app_session, organization_id=user_a.organization_id)
        service_b = CartService(app_session, organization_id=user_b.organization_id)
        cart = await service_a.get_or_create_cart(customer_id=None, session_token="shared-token")

        with pytest.raises(HTTPException) as exc_info:
            await service_b.get_cart(cart.id)
        assert exc_info.value.status_code == 404

    asyncio.run(_run())

