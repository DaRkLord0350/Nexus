import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.barcode import (
    BarcodeCreateRequest,
    BarcodeUpdateRequest,
    QRCodeCreateRequest,
    QRCodeUpdateRequest,
)
from app.schemas.product import ProductCreateRequest
from app.services.auth_service import AuthService
from app.services.barcode_service import BarcodeService
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


async def _register_org(session, email="owner@example.com", org_name="Barcode Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _create_product(session, org_id, user_id):
    product_service = ProductService(session, organization_id=org_id)
    return await product_service.create_product(ProductCreateRequest(name="Widget", sku="WID-1"), created_by=user_id)


def test_create_barcode_for_product(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product = await _create_product(app_session, user.organization_id, user.id)
        service = BarcodeService(app_session, organization_id=user.organization_id)
        barcode = await service.create_barcode(BarcodeCreateRequest(product_id=product.id, value="0123456789012", format="ean13"))
        assert barcode.value == "0123456789012"
        assert barcode.format.value == "ean13"

    asyncio.run(_run())


def test_barcode_requires_exactly_one_owner(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product = await _create_product(app_session, user.organization_id, user.id)
        service = BarcodeService(app_session, organization_id=user.organization_id)

        with pytest.raises(HTTPException) as exc_info:
            await service.create_barcode(BarcodeCreateRequest(value="123"))
        assert exc_info.value.status_code == 400

        with pytest.raises(HTTPException) as exc_info:
            await service.create_barcode(BarcodeCreateRequest(product_id=product.id, variant_id="v1", value="123"))
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_duplicate_value_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product = await _create_product(app_session, user.organization_id, user.id)
        service = BarcodeService(app_session, organization_id=user.organization_id)
        await service.create_barcode(BarcodeCreateRequest(product_id=product.id, value="123", format="code128"))
        with pytest.raises(HTTPException) as exc_info:
            await service.create_barcode(BarcodeCreateRequest(product_id=product.id, value="123", format="code128"))
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_lookup_barcode(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product = await _create_product(app_session, user.organization_id, user.id)
        service = BarcodeService(app_session, organization_id=user.organization_id)
        created = await service.create_barcode(BarcodeCreateRequest(product_id=product.id, value="999", format="upc"))

        found = await service.lookup("999")
        assert found is not None
        assert found.id == created.id

        not_found = await service.lookup("nope")
        assert not_found is None

    asyncio.run(_run())


def test_update_and_bulk_delete_barcode(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product = await _create_product(app_session, user.organization_id, user.id)
        service = BarcodeService(app_session, organization_id=user.organization_id)
        barcode_a = await service.create_barcode(BarcodeCreateRequest(product_id=product.id, value="A1"))
        barcode_b = await service.create_barcode(BarcodeCreateRequest(product_id=product.id, value="A2"))

        updated = await service.update_barcode(barcode_a.id, BarcodeUpdateRequest(is_primary=True))
        assert updated.is_primary is True

        deleted_count = await service.bulk_delete([barcode_a.id, barcode_b.id])
        assert deleted_count == 2
        assert await service.get_barcode(barcode_a.id) is None

    asyncio.run(_run())


def test_qr_code_crud(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product = await _create_product(app_session, user.organization_id, user.id)
        service = BarcodeService(app_session, organization_id=user.organization_id)

        qr = await service.create_qr_code(QRCodeCreateRequest(entity_type="product", entity_id=product.id, value="product-qr-value"))
        assert qr.entity_id == product.id

        with pytest.raises(HTTPException) as exc_info:
            await service.create_qr_code(QRCodeCreateRequest(entity_type="product", entity_id=product.id, value="dup"))
        assert exc_info.value.status_code == 400

        updated = await service.update_qr_code(qr.id, QRCodeUpdateRequest(image_url="https://example.com/qr.png"))
        assert updated.image_url == "https://example.com/qr.png"

        fetched = await service.get_qr_code_for_entity("product", product.id)
        assert fetched.id == qr.id

        await service.delete_qr_code(qr.id)
        assert await service.get_qr_code(qr.id) is None

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        product_a = await _create_product(app_session, user_a.organization_id, user_a.id)

        service_a = BarcodeService(app_session, organization_id=user_a.organization_id)
        service_b = BarcodeService(app_session, organization_id=user_b.organization_id)
        barcode = await service_a.create_barcode(BarcodeCreateRequest(product_id=product_a.id, value="ISO-1"))

        assert await service_b.get_barcode(barcode.id) is None
        assert await service_b.lookup("ISO-1") is None

    asyncio.run(_run())
