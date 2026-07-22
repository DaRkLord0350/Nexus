import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.product import ProductCreateRequest
from app.schemas.product_price import ProductPriceCreateRequest, ProductPriceUpdateRequest
from app.services.auth_service import AuthService
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


async def _setup(session, email="owner@example.com", org_name="Pricing Test Org"):
    auth_service = AuthService(session)
    user = await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )
    product_service = ProductService(session, organization_id=user.organization_id)
    product = await product_service.create_product(ProductCreateRequest(name="T-Shirt", sku="TSHIRT-001"), created_by=user.id)
    return user, product


def test_create_price_and_notify(app_session: AsyncSession):
    async def _run():
        user, product = await _setup(app_session)
        service = PricingService(app_session, organization_id=user.organization_id)
        price = await service.create_price(
            ProductPriceCreateRequest(product_id=product.id, currency="usd", selling_price=19.99, mrp=24.99), created_by=user.id,
        )
        assert price.currency == "USD"

        notifications = await service.notification_service.list_notifications(user.id)
        assert any("price" in n.title.lower() for n in notifications)

    asyncio.run(_run())


def test_resolve_price_prefers_most_specific_match(app_session: AsyncSession):
    async def _run():
        user, product = await _setup(app_session)
        service = PricingService(app_session, organization_id=user.organization_id)

        default_price = await service.create_price(
            ProductPriceCreateRequest(product_id=product.id, currency="USD", selling_price=20), created_by=user.id,
        )
        regional_price = await service.create_price(
            ProductPriceCreateRequest(product_id=product.id, currency="USD", selling_price=25, region="IN"), created_by=user.id,
        )

        resolved_default = await service.resolve_price(product.id, "USD")
        assert resolved_default.id == default_price.id

        resolved_regional = await service.resolve_price(product.id, "USD", region="IN")
        assert resolved_regional.id == regional_price.id

    asyncio.run(_run())


def test_resolve_price_respects_effective_dates(app_session: AsyncSession):
    from datetime import datetime, timedelta

    async def _run():
        user, product = await _setup(app_session)
        service = PricingService(app_session, organization_id=user.organization_id)
        future_only = await service.create_price(
            ProductPriceCreateRequest(
                product_id=product.id, currency="USD", selling_price=15,
                effective_from=datetime.utcnow() + timedelta(days=1),
            ),
            created_by=user.id,
        )
        resolved = await service.resolve_price(product.id, "USD")
        assert resolved is None or resolved.id != future_only.id

    asyncio.run(_run())


def test_invalid_variant_reference_rejected(app_session: AsyncSession):
    async def _run():
        user, product = await _setup(app_session)
        service = PricingService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await service.create_price(
                ProductPriceCreateRequest(product_id=product.id, variant_id="does-not-exist", currency="USD", selling_price=10),
                created_by=user.id,
            )
        assert exc_info.value.status_code == 404

    asyncio.run(_run())


def test_update_price(app_session: AsyncSession):
    async def _run():
        user, product = await _setup(app_session)
        service = PricingService(app_session, organization_id=user.organization_id)
        price = await service.create_price(ProductPriceCreateRequest(product_id=product.id, currency="USD", selling_price=20), created_by=user.id)

        updated = await service.update_price(price.id, ProductPriceUpdateRequest(selling_price=18), actor_id=user.id)
        assert updated.selling_price == 18

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a, product_a = await _setup(app_session, email="a@example.com", org_name="Org A")
        user_b, _ = await _setup(app_session, email="b@example.com", org_name="Org B")

        service_a = PricingService(app_session, organization_id=user_a.organization_id)
        service_b = PricingService(app_session, organization_id=user_b.organization_id)

        price = await service_a.create_price(ProductPriceCreateRequest(product_id=product_a.id, currency="USD", selling_price=20), created_by=user_a.id)
        assert await service_b.get_price(price.id) is None

    asyncio.run(_run())
