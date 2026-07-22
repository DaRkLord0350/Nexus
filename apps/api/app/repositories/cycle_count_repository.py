from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cycle_count import CycleCount, CycleCountStatus
from app.models.cycle_count_item import CycleCountItem
from app.repositories.base_repository import BaseRepository


class CycleCountRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, cycle_count: CycleCount) -> CycleCount:
        self._add_tenant_on_create(cycle_count)
        self.session.add(cycle_count)
        await self.session.commit()
        await self.session.refresh(cycle_count)
        return cycle_count

    async def save(self, cycle_count: CycleCount) -> CycleCount:
        self.session.add(cycle_count)
        await self.session.commit()
        await self.session.refresh(cycle_count)
        return cycle_count

    async def get_by_id(self, cycle_count_id: str) -> CycleCount | None:
        statement = select(CycleCount).where(CycleCount.id == cycle_count_id)
        statement = self._apply_tenant_filter(statement, CycleCount)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_number(self, count_number: str) -> CycleCount | None:
        statement = select(CycleCount).where(CycleCount.count_number == count_number)
        statement = self._apply_tenant_filter(statement, CycleCount)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(self, statement, warehouse_id: str | None = None, status: CycleCountStatus | None = None, q: str | None = None):
        if warehouse_id is not None:
            statement = statement.where(CycleCount.warehouse_id == warehouse_id)
        if status is not None:
            statement = statement.where(CycleCount.status == status)
        if q:
            like = f"%{q}%"
            statement = statement.where(or_(CycleCount.count_number.ilike(like)))
        return statement

    async def list(
        self,
        warehouse_id: str | None = None,
        status: CycleCountStatus | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CycleCount]:
        statement = select(CycleCount).order_by(CycleCount.created_at.desc()).limit(limit).offset(offset)
        statement = self._apply_filters(statement, warehouse_id, status, q)
        statement = self._apply_tenant_filter(statement, CycleCount)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, warehouse_id: str | None = None, status: CycleCountStatus | None = None, q: str | None = None) -> int:
        statement = select(func.count(CycleCount.id))
        statement = self._apply_filters(statement, warehouse_id, status, q)
        statement = self._apply_tenant_filter(statement, CycleCount)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def soft_delete(self, cycle_count_id: str) -> None:
        statement = update(CycleCount).where(CycleCount.id == cycle_count_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, CycleCount)
        await self.session.execute(statement)
        await self.session.commit()


class CycleCountItemRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, item: CycleCountItem) -> CycleCountItem:
        self._add_tenant_on_create(item)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def save(self, item: CycleCountItem) -> CycleCountItem:
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def get_by_id(self, item_id: str) -> CycleCountItem | None:
        statement = select(CycleCountItem).where(CycleCountItem.id == item_id)
        statement = self._apply_tenant_filter(statement, CycleCountItem)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_count(self, cycle_count_id: str) -> list[CycleCountItem]:
        statement = select(CycleCountItem).where(CycleCountItem.cycle_count_id == cycle_count_id).order_by(CycleCountItem.created_at.asc())
        statement = self._apply_tenant_filter(statement, CycleCountItem)
        result = await self.session.execute(statement)
        return result.scalars().all()
