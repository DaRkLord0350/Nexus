import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.product import ProductCreateRequest
from app.schemas.tax import TaxClassCreateRequest, TaxRateCreateRequest
from app.services.auth_service import AuthService
from app.services.product_service import ProductService
from app.services.tax_service import TaxService


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


async def _register_org(session, email="owner@example.com", org_name="Tax Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


def test_create_tax_class_and_rate(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = TaxService(app_session, organization_id=user.organization_id)
        tax_class = await service.create_tax_class(TaxClassCreateRequest(name="Standard GST"), created_by=user.id)
        assert tax_class.code == "standard-gst"

        rate = await service.create_tax_rate(tax_class.id, TaxRateCreateRequest(country="in", rate=18, tax_type="gst"))
        assert rate.country == "IN"

        rates = await service.list_tax_rates(tax_class.id)
        assert len(rates) == 1

    asyncio.run(_run())


def test_calculate_tax_exclusive(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = TaxService(app_session, organization_id=user.organization_id)
        tax_class = await service.create_tax_class(TaxClassCreateRequest(name="Standard GST"), created_by=user.id)
        await service.create_tax_rate(tax_class.id, TaxRateCreateRequest(country="IN", rate=18, tax_type="gst", is_inclusive=False))

        result = await service.calculate_tax(tax_class.id, 100, "IN")
        assert result["tax_amount"] == 18.0
        assert result["total_amount"] == 118.0
        assert result["is_inclusive"] is False

    asyncio.run(_run())


def test_calculate_tax_inclusive(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = TaxService(app_session, organization_id=user.organization_id)
        tax_class = await service.create_tax_class(TaxClassCreateRequest(name="Standard GST"), created_by=user.id)
        await service.create_tax_rate(tax_class.id, TaxRateCreateRequest(country="IN", rate=18, tax_type="gst", is_inclusive=True))

        result = await service.calculate_tax(tax_class.id, 118, "IN")
        assert result["total_amount"] == 118
        assert result["tax_amount"] == pytest.approx(18.0, abs=0.01)

    asyncio.run(_run())


def test_state_specific_rate_overrides_country_default(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = TaxService(app_session, organization_id=user.organization_id)
        tax_class = await service.create_tax_class(TaxClassCreateRequest(name="Sales Tax"), created_by=user.id)
        await service.create_tax_rate(tax_class.id, TaxRateCreateRequest(country="US", rate=5, tax_type="sales_tax"))
        await service.create_tax_rate(tax_class.id, TaxRateCreateRequest(country="US", state="CA", rate=8.5, tax_type="sales_tax"))

        default_result = await service.calculate_tax(tax_class.id, 100, "US")
        assert default_result["rate"] == 5

        ca_result = await service.calculate_tax(tax_class.id, 100, "US", state="CA")
        assert ca_result["rate"] == 8.5

    asyncio.run(_run())


def test_only_one_default_tax_class(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = TaxService(app_session, organization_id=user.organization_id)
        c1 = await service.create_tax_class(TaxClassCreateRequest(name="Standard", is_default=True), created_by=user.id)
        c2 = await service.create_tax_class(TaxClassCreateRequest(name="Reduced", is_default=True), created_by=user.id)

        refreshed_c1 = await service.get_tax_class(c1.id)
        assert refreshed_c1.is_default is False
        assert c2.is_default is True

    asyncio.run(_run())


def test_product_tax_class_reference_validated(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product_service = ProductService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await product_service.create_product(
                ProductCreateRequest(name="Mouse", sku="M-1", tax_class_id="does-not-exist"), created_by=user.id,
            )
        assert exc_info.value.status_code == 404

        tax_service = TaxService(app_session, organization_id=user.organization_id)
        tax_class = await tax_service.create_tax_class(TaxClassCreateRequest(name="Standard"), created_by=user.id)
        product = await product_service.create_product(
            ProductCreateRequest(name="Mouse", sku="M-1", tax_class_id=tax_class.id), created_by=user.id,
        )
        assert product.tax_class_id == tax_class.id

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        service_a = TaxService(app_session, organization_id=user_a.organization_id)
        service_b = TaxService(app_session, organization_id=user_b.organization_id)

        tax_class = await service_a.create_tax_class(TaxClassCreateRequest(name="Standard"), created_by=user_a.id)
        assert await service_b.get_tax_class(tax_class.id) is None

    asyncio.run(_run())
