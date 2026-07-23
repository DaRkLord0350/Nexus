from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pickup import Pickup, PickupStatus
from app.repositories.base_repository import BaseRepository

SORTABLE_FIELDS = {
    "pickup_number": Pickup.pickup_number,
    "scheduled_date": Pickup.scheduled_date,
    "created_at": Pickup.created_at,
}


class PickupRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, pickup: Pickup) -> Pickup:
        self._add_tenant_on_create(pickup)
        self.session.add(pickup)
        await self.session.commit()
        await self.session.refresh(pickup)
        return pickup

    async def save(self, pickup: Pickup) -> Pickup:
        self.session.add(pickup)
        await self.session.commit()
        await self.session.refresh(pickup)
        return pickup

    async def save_no_commit(self, pickup: Pickup) -> Pickup:
        self.session.add(pickup)
        await self.session.flush()
        return pickup

    async def get_by_id(self, pickup_id: str) -> Pickup | None:
        statement = select(Pickup).where(Pickup.id == pickup_id)
        statement = self._apply_tenant_filter(statement, Pickup)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_number(self, pickup_number: str) -> Pickup | None:
        statement = select(Pickup).where(Pickup.pickup_number == pickup_number)
        statement = self._apply_tenant_filter(statement, Pickup)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(self, statement, warehouse_id: str | None = None, status: PickupStatus | None = None):
        if warehouse_id is not None:
            statement = statement.where(Pickup.warehouse_id == warehouse_id)
        if status is not None:
            statement = statement.where(Pickup.status == status)
        return statement

    async def list(
        self,
        warehouse_id: str | None = None,
        status: PickupStatus | None = None,
        sort_by: str = "scheduled_date",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Pickup]:
        column = SORTABLE_FIELDS.get(sort_by, Pickup.scheduled_date)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(Pickup).order_by(order_clause).limit(limit).offset(offset)
        statement = self._apply_filters(statement, warehouse_id, status)
        statement = self._apply_tenant_filter(statement, Pickup)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, warehouse_id: str | None = None, status: PickupStatus | None = None) -> int:
        statement = select(func.count(Pickup.id))
        statement = self._apply_filters(statement, warehouse_id, status)
        statement = self._apply_tenant_filter(statement, Pickup)
        result = await self.session.execute(statement)
        return result.scalar_one()
