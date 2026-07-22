from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.warehouse import Warehouse, WarehouseType
from app.models.warehouse_zone import WarehouseZone
from app.models.warehouse_bin import WarehouseBin
from app.repositories.base_repository import BaseRepository

WAREHOUSE_SORTABLE_FIELDS = {
    "name": Warehouse.name,
    "code": Warehouse.code,
    "created_at": Warehouse.created_at,
    "updated_at": Warehouse.updated_at,
}


class WarehouseRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, warehouse: Warehouse) -> Warehouse:
        self._add_tenant_on_create(warehouse)
        self.session.add(warehouse)
        await self.session.commit()
        await self.session.refresh(warehouse)
        return warehouse

    async def save(self, warehouse: Warehouse) -> Warehouse:
        self.session.add(warehouse)
        await self.session.commit()
        await self.session.refresh(warehouse)
        return warehouse

    async def get_by_id(self, warehouse_id: str) -> Warehouse | None:
        statement = select(Warehouse).where(Warehouse.id == warehouse_id)
        statement = self._apply_tenant_filter(statement, Warehouse)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Warehouse | None:
        statement = select(Warehouse).where(Warehouse.code == code)
        statement = self._apply_tenant_filter(statement, Warehouse)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_default(self) -> Warehouse | None:
        statement = select(Warehouse).where(Warehouse.is_default.is_(True))
        statement = self._apply_tenant_filter(statement, Warehouse)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def clear_default(self, exclude_id: str | None = None) -> None:
        statement = update(Warehouse).where(Warehouse.is_default.is_(True))
        if exclude_id:
            statement = statement.where(Warehouse.id != exclude_id)
        statement = self._apply_tenant_filter(statement, Warehouse)
        statement = statement.values(is_default=False)
        await self.session.execute(statement)
        await self.session.commit()

    def _apply_filters(self, statement, warehouse_type: WarehouseType | None = None, is_active: bool | None = None, q: str | None = None):
        if warehouse_type is not None:
            statement = statement.where(Warehouse.warehouse_type == warehouse_type)
        if is_active is not None:
            statement = statement.where(Warehouse.is_active == is_active)
        if q:
            like = f"%{q}%"
            statement = statement.where(or_(Warehouse.name.ilike(like), Warehouse.code.ilike(like)))
        return statement

    async def list(
        self,
        warehouse_type: WarehouseType | None = None,
        is_active: bool | None = None,
        q: str | None = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Warehouse]:
        column = WAREHOUSE_SORTABLE_FIELDS.get(sort_by, Warehouse.name)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(Warehouse).order_by(order_clause).limit(limit).offset(offset)
        statement = self._apply_filters(statement, warehouse_type, is_active, q)
        statement = self._apply_tenant_filter(statement, Warehouse)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, warehouse_type: WarehouseType | None = None, is_active: bool | None = None, q: str | None = None) -> int:
        statement = select(func.count(Warehouse.id))
        statement = self._apply_filters(statement, warehouse_type, is_active, q)
        statement = self._apply_tenant_filter(statement, Warehouse)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def get_by_id_including_deleted(self, warehouse_id: str) -> Warehouse | None:
        statement = select(Warehouse).where(Warehouse.id == warehouse_id)
        if not self.is_superuser and self.organization_id is not None:
            statement = statement.where(Warehouse.organization_id == self.organization_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def soft_delete(self, warehouse_id: str) -> None:
        statement = update(Warehouse).where(Warehouse.id == warehouse_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Warehouse)
        await self.session.execute(statement)
        await self.session.commit()

    async def restore(self, warehouse_id: str) -> Warehouse | None:
        statement = update(Warehouse).where(Warehouse.id == warehouse_id).values(deleted_at=None)
        if not self.is_superuser and self.organization_id is not None:
            statement = statement.where(Warehouse.organization_id == self.organization_id)
        await self.session.execute(statement)
        await self.session.commit()
        return await self.get_by_id(warehouse_id)

    async def bulk_soft_delete(self, warehouse_ids: list[str]) -> int:
        if not warehouse_ids:
            return 0
        statement = update(Warehouse).where(Warehouse.id.in_(warehouse_ids)).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Warehouse)
        result = await self.session.execute(statement)
        await self.session.commit()
        return result.rowcount or 0


class WarehouseZoneRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, zone: WarehouseZone) -> WarehouseZone:
        self._add_tenant_on_create(zone)
        self.session.add(zone)
        await self.session.commit()
        await self.session.refresh(zone)
        return zone

    async def save(self, zone: WarehouseZone) -> WarehouseZone:
        self.session.add(zone)
        await self.session.commit()
        await self.session.refresh(zone)
        return zone

    async def get_by_id(self, zone_id: str) -> WarehouseZone | None:
        statement = select(WarehouseZone).where(WarehouseZone.id == zone_id)
        statement = self._apply_tenant_filter(statement, WarehouseZone)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_code(self, warehouse_id: str, code: str) -> WarehouseZone | None:
        statement = select(WarehouseZone).where(WarehouseZone.warehouse_id == warehouse_id, WarehouseZone.code == code)
        statement = self._apply_tenant_filter(statement, WarehouseZone)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_warehouse(self, warehouse_id: str, limit: int = 200, offset: int = 0) -> list[WarehouseZone]:
        statement = (
            select(WarehouseZone)
            .where(WarehouseZone.warehouse_id == warehouse_id)
            .order_by(WarehouseZone.name.asc())
            .limit(limit)
            .offset(offset)
        )
        statement = self._apply_tenant_filter(statement, WarehouseZone)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count_for_warehouse(self, warehouse_id: str) -> int:
        statement = select(func.count(WarehouseZone.id)).where(WarehouseZone.warehouse_id == warehouse_id)
        statement = self._apply_tenant_filter(statement, WarehouseZone)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def soft_delete(self, zone_id: str) -> None:
        statement = update(WarehouseZone).where(WarehouseZone.id == zone_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, WarehouseZone)
        await self.session.execute(statement)
        await self.session.commit()


class WarehouseBinRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, bin_: WarehouseBin) -> WarehouseBin:
        self._add_tenant_on_create(bin_)
        self.session.add(bin_)
        await self.session.commit()
        await self.session.refresh(bin_)
        return bin_

    async def save(self, bin_: WarehouseBin) -> WarehouseBin:
        self.session.add(bin_)
        await self.session.commit()
        await self.session.refresh(bin_)
        return bin_

    async def get_by_id(self, bin_id: str) -> WarehouseBin | None:
        statement = select(WarehouseBin).where(WarehouseBin.id == bin_id)
        statement = self._apply_tenant_filter(statement, WarehouseBin)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_code(self, warehouse_id: str, code: str) -> WarehouseBin | None:
        statement = select(WarehouseBin).where(WarehouseBin.warehouse_id == warehouse_id, WarehouseBin.code == code)
        statement = self._apply_tenant_filter(statement, WarehouseBin)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(self, statement, zone_id: str | None = None, q: str | None = None):
        if zone_id is not None:
            statement = statement.where(WarehouseBin.zone_id == zone_id)
        if q:
            like = f"%{q}%"
            statement = statement.where(WarehouseBin.code.ilike(like))
        return statement

    async def list_for_warehouse(
        self,
        warehouse_id: str,
        zone_id: str | None = None,
        q: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[WarehouseBin]:
        statement = (
            select(WarehouseBin)
            .where(WarehouseBin.warehouse_id == warehouse_id)
            .order_by(WarehouseBin.code.asc())
            .limit(limit)
            .offset(offset)
        )
        statement = self._apply_filters(statement, zone_id, q)
        statement = self._apply_tenant_filter(statement, WarehouseBin)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count_for_warehouse(self, warehouse_id: str, zone_id: str | None = None, q: str | None = None) -> int:
        statement = select(func.count(WarehouseBin.id)).where(WarehouseBin.warehouse_id == warehouse_id)
        statement = self._apply_filters(statement, zone_id, q)
        statement = self._apply_tenant_filter(statement, WarehouseBin)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def soft_delete(self, bin_id: str) -> None:
        statement = update(WarehouseBin).where(WarehouseBin.id == bin_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, WarehouseBin)
        await self.session.execute(statement)
        await self.session.commit()
