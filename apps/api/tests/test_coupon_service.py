import asyncio
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.coupon import CouponCreateRequest
from app.schemas.product import ProductCreateRequest
from app.services.auth_service import AuthService
from app.services.coupon_service import CouponService
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


async def _register_org(session, email="owner@example.com", org_name="Coupon Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


def test_create_coupon_uppercases_code(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CouponService(app_session, organization_id=user.organization_id)
        coupon = await service.create_coupon(CouponCreateRequest(code="summer20", discount_type="percentage", discount_value=20), created_by=user.id)
        assert coupon.code == "SUMMER20"

    asyncio.run(_run())


def test_duplicate_code_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CouponService(app_session, organization_id=user.organization_id)
        await service.create_coupon(CouponCreateRequest(code="SUMMER20", discount_value=20), created_by=user.id)
        with pytest.raises(HTTPException) as exc_info:
            await service.create_coupon(CouponCreateRequest(code="summer20", discount_value=10), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_validate_percentage_coupon_with_max_discount(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CouponService(app_session, organization_id=user.organization_id)
        await service.create_coupon(
            CouponCreateRequest(code="SAVE20", discount_type="percentage", discount_value=20, max_discount_amount=15), created_by=user.id,
        )

        result = await service.validate_coupon("SAVE20", order_amount=100)
        assert result["valid"] is True
        assert result["discount_amount"] == 15

    asyncio.run(_run())


def test_validate_respects_min_order_amount(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CouponService(app_session, organization_id=user.organization_id)
        await service.create_coupon(
            CouponCreateRequest(code="BIGORDER", discount_type="fixed_amount", discount_value=10, min_order_amount=50), created_by=user.id,
        )

        result = await service.validate_coupon("BIGORDER", order_amount=30)
        assert result["valid"] is False
        assert "at least" in result["reason"]

    asyncio.run(_run())


def test_buy_x_get_y_discount_calculation(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CouponService(app_session, organization_id=user.organization_id)
        await service.create_coupon(
            CouponCreateRequest(code="B2G1", discount_type="buy_x_get_y", buy_quantity=2, get_quantity=1, get_discount_percentage=100),
            created_by=user.id,
        )

        result = await service.validate_coupon("B2G1", order_amount=90, quantity=6, unit_price=10)
        assert result["valid"] is True
        assert result["discount_amount"] == 20.0

    asyncio.run(_run())


def test_product_restriction_enforced(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product_service = ProductService(app_session, organization_id=user.organization_id)
        eligible = await product_service.create_product(ProductCreateRequest(name="Eligible", sku="E-1"), created_by=user.id)
        await product_service.create_product(ProductCreateRequest(name="Not Eligible", sku="N-1"), created_by=user.id)

        service = CouponService(app_session, organization_id=user.organization_id)
        coupon = await service.create_coupon(
            CouponCreateRequest(code="PRODUCTONLY", discount_value=10, product_ids=[eligible.id]), created_by=user.id,
        )
        assert coupon.product_ids == [eligible.id]

        matching = await service.validate_coupon("PRODUCTONLY", order_amount=100, product_ids=[eligible.id])
        assert matching["valid"] is True

        non_matching = await service.validate_coupon("PRODUCTONLY", order_amount=100, product_ids=["some-other-id"])
        assert non_matching["valid"] is False

    asyncio.run(_run())


def test_usage_limit_enforced_after_redeem(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CouponService(app_session, organization_id=user.organization_id)
        coupon = await service.create_coupon(CouponCreateRequest(code="ONEUSE", discount_value=5, usage_limit=1), created_by=user.id)

        await service.redeem_coupon(coupon.id)
        result = await service.validate_coupon("ONEUSE", order_amount=100)
        assert result["valid"] is False
        assert "usage limit" in result["reason"].lower()

    asyncio.run(_run())


def test_expired_coupon_deactivated_and_notifies(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CouponService(app_session, organization_id=user.organization_id)
        await service.create_coupon(
            CouponCreateRequest(code="EXPIRED", discount_value=10, expires_at=datetime.utcnow() - timedelta(days=1)), created_by=user.id,
        )

        result = await service.validate_coupon("EXPIRED", order_amount=100)
        assert result["valid"] is False

        notifications = await service.notification_service.list_notifications(user.id)
        assert any("expired" in n.title.lower() for n in notifications)

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        service_a = CouponService(app_session, organization_id=user_a.organization_id)
        service_b = CouponService(app_session, organization_id=user_b.organization_id)

        coupon = await service_a.create_coupon(CouponCreateRequest(code="SAVE10", discount_value=10), created_by=user_a.id)
        assert await service_b.get_coupon(coupon.id) is None

    asyncio.run(_run())
