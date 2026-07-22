from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.warehouse import Warehouse, WarehouseType
from app.models.warehouse_bin import WarehouseBin, WarehouseBinStatus
from app.models.warehouse_zone import WarehouseZone, WarehouseZoneType
from app.repositories.warehouse_repository import (
    WarehouseBinRepository,
    WarehouseRepository,
    WarehouseZoneRepository,
)


class WarehouseService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = WarehouseRepository(session, organization_id, is_superuser)
        self.zone_repo = WarehouseZoneRepository(session, organization_id, is_superuser)
        self.bin_repo = WarehouseBinRepository(session, organization_id, is_superuser)

    async def _ensure_unique_code(self, code: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_code(code)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A warehouse with that code already exists.")

    async def create_warehouse(self, data, created_by: str | None = None) -> Warehouse:
        await self._ensure_unique_code(data.code)
        warehouse = Warehouse(
            name=data.name,
            code=data.code,
            warehouse_type=WarehouseType(data.warehouse_type.value),
            email=data.email,
            phone=data.phone,
            country=data.country,
            state=data.state,
            city=data.city,
            zipcode=data.zipcode,
            address=data.address,
            is_default=data.is_default,
            is_active=data.is_active,
            created_by=created_by,
        )
        warehouse = await self.repo.create(warehouse)
        if warehouse.is_default:
            await self.repo.clear_default(exclude_id=warehouse.id)
        return warehouse

    async def update_warehouse(self, warehouse_id: str, data) -> Warehouse:
        warehouse = await self.repo.get_by_id(warehouse_id)
        if not warehouse:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found.")

        if data.code is not None and data.code != warehouse.code:
            await self._ensure_unique_code(data.code, exclude_id=warehouse.id)

        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            if field == "warehouse_type" and value is not None:
                value = WarehouseType(value.value if hasattr(value, "value") else value)
            setattr(warehouse, field, value)

        warehouse = await self.repo.save(warehouse)
        if warehouse.is_default:
            await self.repo.clear_default(exclude_id=warehouse.id)
        return warehouse

    async def delete_warehouse(self, warehouse_id: str) -> None:
        warehouse = await self.repo.get_by_id(warehouse_id)
        if not warehouse:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found.")
        await self.repo.soft_delete(warehouse_id)

    async def bulk_delete(self, warehouse_ids: list[str]) -> int:
        return await self.repo.bulk_soft_delete(warehouse_ids)

    async def restore_warehouse(self, warehouse_id: str) -> Warehouse:
        warehouse = await self.repo.get_by_id_including_deleted(warehouse_id)
        if not warehouse:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found.")
        if warehouse.deleted_at is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Warehouse is not deleted.")
        return await self.repo.restore(warehouse_id)

    async def get_warehouse(self, warehouse_id: str) -> Warehouse | None:
        return await self.repo.get_by_id(warehouse_id)

    async def set_default(self, warehouse_id: str) -> Warehouse:
        warehouse = await self.repo.get_by_id(warehouse_id)
        if not warehouse:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found.")
        warehouse.is_default = True
        warehouse = await self.repo.save(warehouse)
        await self.repo.clear_default(exclude_id=warehouse.id)
        return warehouse

    async def list_warehouses(
        self,
        warehouse_type: WarehouseType | None = None,
        is_active: bool | None = None,
        q: str | None = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Warehouse], int]:
        items = await self.repo.list(warehouse_type, is_active, q, sort_by, sort_order, limit, offset)
        total = await self.repo.count(warehouse_type, is_active, q)
        return items, total

    async def _get_warehouse_or_404(self, warehouse_id: str) -> Warehouse:
        warehouse = await self.repo.get_by_id(warehouse_id)
        if not warehouse:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found.")
        return warehouse

    async def _ensure_unique_zone_code(self, warehouse_id: str, code: str, exclude_id: str | None = None) -> None:
        existing = await self.zone_repo.get_by_code(warehouse_id, code)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A zone with that code already exists in this warehouse.")

    async def create_zone(self, warehouse_id: str, data) -> WarehouseZone:
        await self._get_warehouse_or_404(warehouse_id)
        await self._ensure_unique_zone_code(warehouse_id, data.code)
        zone = WarehouseZone(
            warehouse_id=warehouse_id,
            name=data.name,
            code=data.code,
            zone_type=WarehouseZoneType(data.zone_type.value),
            description=data.description,
            is_active=data.is_active,
        )
        return await self.zone_repo.create(zone)

    async def update_zone(self, warehouse_id: str, zone_id: str, data) -> WarehouseZone:
        zone = await self.zone_repo.get_by_id(zone_id)
        if not zone or zone.warehouse_id != warehouse_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse zone not found.")

        if data.code is not None and data.code != zone.code:
            await self._ensure_unique_zone_code(warehouse_id, data.code, exclude_id=zone.id)

        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            if field == "zone_type" and value is not None:
                value = WarehouseZoneType(value.value if hasattr(value, "value") else value)
            setattr(zone, field, value)

        return await self.zone_repo.save(zone)

    async def delete_zone(self, warehouse_id: str, zone_id: str) -> None:
        zone = await self.zone_repo.get_by_id(zone_id)
        if not zone or zone.warehouse_id != warehouse_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse zone not found.")
        await self.zone_repo.soft_delete(zone_id)

    async def list_zones(self, warehouse_id: str, limit: int = 200, offset: int = 0) -> tuple[list[WarehouseZone], int]:
        await self._get_warehouse_or_404(warehouse_id)
        items = await self.zone_repo.list_for_warehouse(warehouse_id, limit, offset)
        total = await self.zone_repo.count_for_warehouse(warehouse_id)
        return items, total

    async def _ensure_unique_bin_code(self, warehouse_id: str, code: str, exclude_id: str | None = None) -> None:
        existing = await self.bin_repo.get_by_code(warehouse_id, code)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A bin with that code already exists in this warehouse.")

    async def create_bin(self, warehouse_id: str, data) -> WarehouseBin:
        await self._get_warehouse_or_404(warehouse_id)
        await self._ensure_unique_bin_code(warehouse_id, data.code)
        if data.zone_id:
            zone = await self.zone_repo.get_by_id(data.zone_id)
            if not zone or zone.warehouse_id != warehouse_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Zone does not belong to this warehouse.")
        bin_ = WarehouseBin(
            warehouse_id=warehouse_id,
            zone_id=data.zone_id,
            code=data.code,
            aisle=data.aisle,
            rack=data.rack,
            shelf=data.shelf,
            bin_number=data.bin_number,
            capacity=data.capacity,
            status=WarehouseBinStatus(data.status.value),
        )
        return await self.bin_repo.create(bin_)

    async def update_bin(self, warehouse_id: str, bin_id: str, data) -> WarehouseBin:
        bin_ = await self.bin_repo.get_by_id(bin_id)
        if not bin_ or bin_.warehouse_id != warehouse_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse bin not found.")

        if data.code is not None and data.code != bin_.code:
            await self._ensure_unique_bin_code(warehouse_id, data.code, exclude_id=bin_.id)
        if data.zone_id is not None and data.zone_id != bin_.zone_id:
            zone = await self.zone_repo.get_by_id(data.zone_id)
            if not zone or zone.warehouse_id != warehouse_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Zone does not belong to this warehouse.")

        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            if field == "status" and value is not None:
                value = WarehouseBinStatus(value.value if hasattr(value, "value") else value)
            setattr(bin_, field, value)

        return await self.bin_repo.save(bin_)

    async def delete_bin(self, warehouse_id: str, bin_id: str) -> None:
        bin_ = await self.bin_repo.get_by_id(bin_id)
        if not bin_ or bin_.warehouse_id != warehouse_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse bin not found.")
        await self.bin_repo.soft_delete(bin_id)

    async def list_bins(
        self,
        warehouse_id: str,
        zone_id: str | None = None,
        q: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> tuple[list[WarehouseBin], int]:
        await self._get_warehouse_or_404(warehouse_id)
        items = await self.bin_repo.list_for_warehouse(warehouse_id, zone_id, q, limit, offset)
        total = await self.bin_repo.count_for_warehouse(warehouse_id, zone_id, q)
        return items, total
