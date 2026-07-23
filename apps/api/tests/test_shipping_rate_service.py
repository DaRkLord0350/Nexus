import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.shipping_provider import ShippingProviderCreateRequest
from app.schemas.shipping_rate import RateCompareRequest, ShippingRateCreateRequest
from app.services.auth_service import AuthService
from app.services.shipping_provider_service import ShippingProviderService
from app.services.shipping_rate_service import ShippingRateService


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


async def _register_org(session, email="owner@example.com", org_name="Rate Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


def test_compute_cost_includes_weight_and_cod(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        provider_service = ShippingProviderService(app_session, organization_id=user.organization_id)
        provider = await provider_service.create_provider(ShippingProviderCreateRequest(name="Delhivery", code="delhivery"), created_by=user.id)

        rate_service = ShippingRateService(app_session, organization_id=user.organization_id)
        rate = await rate_service.create_rate(ShippingRateCreateRequest(
            shipping_provider_id=provider.id, name="Zone A", destination_country="IN",
            base_price=50, price_per_kg=10, min_weight=1, cod_fee=20, transit_days_min=2, transit_days_max=4,
        ), created_by=user.id)

        cost = rate_service._compute_cost(rate, weight=3, is_cod=True, needs_insurance=False)
        assert cost == 50 + (3 - 1) * 10 + 20

    asyncio.run(_run())


def test_compare_rates_recommends_best_score(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        provider_service = ShippingProviderService(app_session, organization_id=user.organization_id)
        cheap_slow = await provider_service.create_provider(ShippingProviderCreateRequest(name="Cheap Slow", code="cheap-slow"), created_by=user.id)
        fast_expensive = await provider_service.create_provider(ShippingProviderCreateRequest(name="Fast Expensive", code="fast-expensive"), created_by=user.id)

        rate_service = ShippingRateService(app_session, organization_id=user.organization_id)
        await rate_service.create_rate(ShippingRateCreateRequest(
            shipping_provider_id=cheap_slow.id, name="Zone A", destination_country="IN",
            base_price=30, transit_days_min=5, transit_days_max=7, delivery_rating=4.0,
        ), created_by=user.id)
        await rate_service.create_rate(ShippingRateCreateRequest(
            shipping_provider_id=fast_expensive.id, name="Zone A", destination_country="IN",
            base_price=100, transit_days_min=1, transit_days_max=1, delivery_rating=4.5,
        ), created_by=user.id)

        quotes = await rate_service.compare_rates(RateCompareRequest(destination_country="IN", weight=1.0))
        assert len(quotes) == 2
        recommended = [q for q in quotes if q["recommended"]]
        assert len(recommended) == 1

    asyncio.run(_run())


def test_compare_rates_excludes_non_cod_providers(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        provider_service = ShippingProviderService(app_session, organization_id=user.organization_id)
        cod_provider = await provider_service.create_provider(ShippingProviderCreateRequest(name="COD Capable", code="cod-ok", supports_cod=True, base_rate=25), created_by=user.id)
        no_cod_provider = await provider_service.create_provider(ShippingProviderCreateRequest(name="No COD", code="no-cod", supports_cod=False, base_rate=15), created_by=user.id)

        rate_service = ShippingRateService(app_session, organization_id=user.organization_id)
        quotes = await rate_service.compare_rates(RateCompareRequest(destination_country="US", weight=1.0, is_cod=True))

        provider_ids = {q["shipping_provider_id"] for q in quotes}
        assert cod_provider.id in provider_ids
        assert no_cod_provider.id not in provider_ids

    asyncio.run(_run())


def test_compare_rates_falls_back_to_provider_base_rate(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        provider_service = ShippingProviderService(app_session, organization_id=user.organization_id)
        provider = await provider_service.create_provider(ShippingProviderCreateRequest(name="Manual Courier", code="manual", base_rate=40, base_transit_days=3), created_by=user.id)

        rate_service = ShippingRateService(app_session, organization_id=user.organization_id)
        quotes = await rate_service.compare_rates(RateCompareRequest(destination_country="US", weight=1.0))

        assert len(quotes) == 1
        assert quotes[0]["cost"] == 40
        assert quotes[0]["rate_id"] is None

    asyncio.run(_run())


def test_update_and_delete_rate(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        provider_service = ShippingProviderService(app_session, organization_id=user.organization_id)
        provider = await provider_service.create_provider(ShippingProviderCreateRequest(name="A", code="a"), created_by=user.id)

        rate_service = ShippingRateService(app_session, organization_id=user.organization_id)
        rate = await rate_service.create_rate(ShippingRateCreateRequest(shipping_provider_id=provider.id, name="Zone A", base_price=10), created_by=user.id)

        from app.schemas.shipping_rate import ShippingRateUpdateRequest
        updated = await rate_service.update_rate(rate.id, ShippingRateUpdateRequest(base_price=99))
        assert updated.base_price == 99

        await rate_service.delete_rate(rate.id)
        assert await rate_service.get_rate(rate.id) is None

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")

        provider_service_a = ShippingProviderService(app_session, organization_id=user_a.organization_id)
        provider_a = await provider_service_a.create_provider(ShippingProviderCreateRequest(name="A", code="a"), created_by=user_a.id)

        rate_service_a = ShippingRateService(app_session, organization_id=user_a.organization_id)
        rate = await rate_service_a.create_rate(ShippingRateCreateRequest(shipping_provider_id=provider_a.id, name="Zone A", base_price=10), created_by=user_a.id)

        rate_service_b = ShippingRateService(app_session, organization_id=user_b.organization_id)
        assert await rate_service_b.get_rate(rate.id) is None

    asyncio.run(_run())

