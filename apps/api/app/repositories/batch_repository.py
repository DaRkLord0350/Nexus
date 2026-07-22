from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.batch import Batch, BatchStatus
from app.repositories.base_repository import BaseRepository

SORTABLE_FIELDS = {
    "batch_number": Batch.batch_number,
    "expiry_date": Batch.expiry_date,
    "created_at": Batch.created_at,
    "remaining_quantity": Batch.remaining_quantity,
}


class BatchRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, batch: Batch) -> Batch:
        self._add_tenant_on_create(batch)
        self.session.add(batch)
        await self.session.commit()
        await self.session.refresh(batch)
        return batch

    async def create_no_commit(self, batch: Batch) -> Batch:
        self._add_tenant_on_create(batch)
        self.session.add(batch)
        await self.session.flush()
        return batch

    async def save(self, batch: Batch) -> Batch:
        self.session.add(batch)
        await self.session.commit()
        await self.session.refresh(batch)
        return batch

    async def save_no_commit(self, batch: Batch) -> Batch:
        self.session.add(batch)
        await self.session.flush()
        return batch

    async def get_by_id(self, batch_id: str) -> Batch | None:
        statement = select(Batch).where(Batch.id == batch_id)
        statement = self._apply_tenant_filter(statement, Batch)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_number(self, product_id: str, warehouse_id: str, batch_number: str) -> Batch | None:
        statement = select(Batch).where(
            Batch.product_id == product_id,
            Batch.warehouse_id == warehouse_id,
            Batch.batch_number == batch_number,
        )
        statement = self._apply_tenant_filter(statement, Batch)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(
        self,
        statement,
        product_id: str | None = None,
        warehouse_id: str | None = None,
        status: BatchStatus | None = None,
        expiring_before: datetime | None = None,
        q: str | None = None,
    ):
        if product_id is not None:
            statement = statement.where(Batch.product_id == product_id)
        if warehouse_id is not None:
            statement = statement.where(Batch.warehouse_id == warehouse_id)
        if status is not None:
            statement = statement.where(Batch.status == status)
        if expiring_before is not None:
            statement = statement.where(Batch.expiry_date.is_not(None), Batch.expiry_date <= expiring_before)
        if q:
            like = f"%{q}%"
            statement = statement.where(or_(Batch.batch_number.ilike(like)))
        return statement

    async def list(
        self,
        product_id: str | None = None,
        warehouse_id: str | None = None,
        status: BatchStatus | None = None,
        expiring_before: datetime | None = None,
        q: str | None = None,
        sort_by: str = "expiry_date",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Batch]:
        column = SORTABLE_FIELDS.get(sort_by, Batch.expiry_date)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(Batch).order_by(order_clause).limit(limit).offset(offset)
        statement = self._apply_filters(statement, product_id, warehouse_id, status, expiring_before, q)
        statement = self._apply_tenant_filter(statement, Batch)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(
        self,
        product_id: str | None = None,
        warehouse_id: str | None = None,
        status: BatchStatus | None = None,
        expiring_before: datetime | None = None,
        q: str | None = None,
    ) -> int:
        statement = select(func.count(Batch.id))
        statement = self._apply_filters(statement, product_id, warehouse_id, status, expiring_before, q)
        statement = self._apply_tenant_filter(statement, Batch)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def soft_delete(self, batch_id: str) -> None:
        statement = update(Batch).where(Batch.id == batch_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Batch)
        await self.session.execute(statement)
        await self.session.commit()
