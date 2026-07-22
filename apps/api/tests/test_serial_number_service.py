import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.product import ProductCreateRequest
from app.schemas.serial_number import (
    SerialNumberBulkImportRequest,
    SerialNumberCreateRequest,
    SerialNumberUpdateRequest,
)
from app.schemas.warehouse import WarehouseCreateRequest
from app.services.auth_service import AuthService
from app.services.product_service import ProductService
from app.services.serial_number_service import SerialNumberService
from app.services.warehouse_service import WarehouseService


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


async def _register_org(session, email="owner@example.com", org_name="Serial Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _setup_product_and_warehouse(session, org_id, user_id):
    product_service = ProductService(session, organization_id=org_id)
    product = await product_service.create_product(ProductCreateRequest(name="Laptop", sku="LAP-1"), created_by=user_id)
    warehouse_service = WarehouseService(session, organization_id=org_id)
    warehouse = await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Main", code="MAIN"), created_by=user_id)
    return product, warehouse


def test_create_serial(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = SerialNumberService(app_session, organization_id=user.organization_id)

        serial = await service.create_serial(SerialNumberCreateRequest(product_id=product.id, warehouse_id=warehouse.id, serial="SN-001"))
        assert serial.serial == "SN-001"
        assert serial.status.value == "available"
        assert serial.inventory_id is not None

    asyncio.run(_run())


def test_duplicate_serial_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = SerialNumberService(app_session, organization_id=user.organization_id)
        await service.create_serial(SerialNumberCreateRequest(product_id=product.id, warehouse_id=warehouse.id, serial="SN-001"))
        with pytest.raises(HTTPException) as exc_info:
            await service.create_serial(SerialNumberCreateRequest(product_id=product.id, warehouse_id=warehouse.id, serial="SN-001"))
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_bulk_import_skips_duplicates(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = SerialNumberService(app_session, organization_id=user.organization_id)
        await service.create_serial(SerialNumberCreateRequest(product_id=product.id, warehouse_id=warehouse.id, serial="SN-EXIST"))

        created, skipped = await service.bulk_import(SerialNumberBulkImportRequest(
            product_id=product.id, warehouse_id=warehouse.id, serials=["SN-1", "SN-2", "SN-EXIST"],
        ))
        assert len(created) == 2
        assert skipped == ["SN-EXIST"]

    asyncio.run(_run())


def test_update_status_sets_sold_at(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = SerialNumberService(app_session, organization_id=user.organization_id)
        serial = await service.create_serial(SerialNumberCreateRequest(product_id=product.id, warehouse_id=warehouse.id, serial="SN-001"))
        assert serial.sold_at is None

        updated = await service.update_serial(serial.id, SerialNumberUpdateRequest(status="sold"))
        assert updated.status.value == "sold"
        assert updated.sold_at is not None

    asyncio.run(_run())


def test_scan_serial(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = SerialNumberService(app_session, organization_id=user.organization_id)
        created = await service.create_serial(SerialNumberCreateRequest(product_id=product.id, warehouse_id=warehouse.id, serial="SCAN-ME"))

        found = await service.scan("SCAN-ME")
        assert found.id == created.id
        assert await service.scan("NOPE") is None

    asyncio.run(_run())


def test_delete_and_bulk_delete(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = SerialNumberService(app_session, organization_id=user.organization_id)
        s1 = await service.create_serial(SerialNumberCreateRequest(product_id=product.id, warehouse_id=warehouse.id, serial="SN-A"))
        s2 = await service.create_serial(SerialNumberCreateRequest(product_id=product.id, warehouse_id=warehouse.id, serial="SN-B"))

        deleted_count = await service.bulk_delete([s1.id, s2.id])
        assert deleted_count == 2
        assert await service.get_serial(s1.id) is None

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        product_a, warehouse_a = await _setup_product_and_warehouse(app_session, user_a.organization_id, user_a.id)

        service_a = SerialNumberService(app_session, organization_id=user_a.organization_id)
        service_b = SerialNumberService(app_session, organization_id=user_b.organization_id)
        serial = await service_a.create_serial(SerialNumberCreateRequest(product_id=product_a.id, warehouse_id=warehouse_a.id, serial="ISO-1"))

        assert await service_b.get_serial(serial.id) is None
        assert await service_b.scan("ISO-1") is None

    asyncio.run(_run())
