import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.warehouse import (
    WarehouseBinCreateRequest,
    WarehouseBinUpdateRequest,
    WarehouseCreateRequest,
    WarehouseUpdateRequest,
    WarehouseZoneCreateRequest,
    WarehouseZoneUpdateRequest,
)
from app.services.auth_service import AuthService
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


async def _register_org(session, email="owner@example.com", org_name="Warehouse Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


def test_create_warehouse(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = WarehouseService(app_session, organization_id=user.organization_id)
        warehouse = await service.create_warehouse(WarehouseCreateRequest(name="Main DC", code="MAIN"), created_by=user.id)
        assert warehouse.code == "MAIN"
        assert warehouse.warehouse_type.value == "main"

    asyncio.run(_run())


def test_duplicate_code_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = WarehouseService(app_session, organization_id=user.organization_id)
        await service.create_warehouse(WarehouseCreateRequest(name="Main DC", code="MAIN"), created_by=user.id)
        with pytest.raises(HTTPException) as exc_info:
            await service.create_warehouse(WarehouseCreateRequest(name="Other DC", code="MAIN"), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_only_one_default_warehouse(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = WarehouseService(app_session, organization_id=user.organization_id)
        wh_a = await service.create_warehouse(WarehouseCreateRequest(name="A", code="A", is_default=True), created_by=user.id)
        wh_b = await service.create_warehouse(WarehouseCreateRequest(name="B", code="B", is_default=True), created_by=user.id)

        refreshed_a = await service.get_warehouse(wh_a.id)
        assert refreshed_a.is_default is False
        refreshed_b = await service.get_warehouse(wh_b.id)
        assert refreshed_b.is_default is True

        promoted = await service.set_default(wh_a.id)
        assert promoted.is_default is True
        refreshed_b_again = await service.get_warehouse(wh_b.id)
        assert refreshed_b_again.is_default is False

    asyncio.run(_run())


def test_update_and_bulk_delete(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = WarehouseService(app_session, organization_id=user.organization_id)
        wh_a = await service.create_warehouse(WarehouseCreateRequest(name="A", code="A"), created_by=user.id)
        wh_b = await service.create_warehouse(WarehouseCreateRequest(name="B", code="B"), created_by=user.id)

        updated = await service.update_warehouse(wh_a.id, WarehouseUpdateRequest(is_active=False))
        assert updated.is_active is False

        deleted_count = await service.bulk_delete([wh_a.id, wh_b.id])
        assert deleted_count == 2
        assert await service.get_warehouse(wh_a.id) is None
        assert await service.get_warehouse(wh_b.id) is None

    asyncio.run(_run())


def test_restore_warehouse(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = WarehouseService(app_session, organization_id=user.organization_id)
        warehouse = await service.create_warehouse(WarehouseCreateRequest(name="A", code="A"), created_by=user.id)
        await service.delete_warehouse(warehouse.id)
        assert await service.get_warehouse(warehouse.id) is None
        restored = await service.restore_warehouse(warehouse.id)
        assert restored.id == warehouse.id

    asyncio.run(_run())


def test_zone_and_bin_crud(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = WarehouseService(app_session, organization_id=user.organization_id)
        warehouse = await service.create_warehouse(WarehouseCreateRequest(name="Main DC", code="MAIN"), created_by=user.id)

        zone = await service.create_zone(warehouse.id, WarehouseZoneCreateRequest(name="Storage A", code="A"))
        assert zone.warehouse_id == warehouse.id

        with pytest.raises(HTTPException) as exc_info:
            await service.create_zone(warehouse.id, WarehouseZoneCreateRequest(name="Dup", code="A"))
        assert exc_info.value.status_code == 400

        updated_zone = await service.update_zone(warehouse.id, zone.id, WarehouseZoneUpdateRequest(is_active=False))
        assert updated_zone.is_active is False

        bin_ = await service.create_bin(warehouse.id, WarehouseBinCreateRequest(zone_id=zone.id, code="A-01-01"))
        assert bin_.zone_id == zone.id

        updated_bin = await service.update_bin(warehouse.id, bin_.id, WarehouseBinUpdateRequest(capacity=100))
        assert updated_bin.capacity == 100

        zones, zone_total = await service.list_zones(warehouse.id)
        assert zone_total == 1
        bins, bin_total = await service.list_bins(warehouse.id)
        assert bin_total == 1

        await service.delete_bin(warehouse.id, bin_.id)
        await service.delete_zone(warehouse.id, zone.id)
        _, zone_total_after = await service.list_zones(warehouse.id)
        assert zone_total_after == 0

    asyncio.run(_run())


def test_bin_zone_must_belong_to_same_warehouse(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = WarehouseService(app_session, organization_id=user.organization_id)
        warehouse_a = await service.create_warehouse(WarehouseCreateRequest(name="A", code="A"), created_by=user.id)
        warehouse_b = await service.create_warehouse(WarehouseCreateRequest(name="B", code="B"), created_by=user.id)
        zone_b = await service.create_zone(warehouse_b.id, WarehouseZoneCreateRequest(name="Zone B", code="Z"))

        with pytest.raises(HTTPException) as exc_info:
            await service.create_bin(warehouse_a.id, WarehouseBinCreateRequest(zone_id=zone_b.id, code="X"))
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        service_a = WarehouseService(app_session, organization_id=user_a.organization_id)
        service_b = WarehouseService(app_session, organization_id=user_b.organization_id)
        warehouse = await service_a.create_warehouse(WarehouseCreateRequest(name="A", code="A"), created_by=user_a.id)
        assert await service_b.get_warehouse(warehouse.id) is None

    asyncio.run(_run())
