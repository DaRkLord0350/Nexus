from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock_adjustment import StockAdjustment, StockAdjustmentReason
from app.repositories.base_repository import BaseRepository


class StockAdjustmentRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, adjustment: StockAdjustment) -> StockAdjustment:
        self._add_tenant_on_create(adjustment)
        self.session.add(adjustment)
        await self.session.commit()
        await self.session.refresh(adjustment)
        return adjustment

    async def get_by_id(self, adjustment_id: str) -> StockAdjustment | None:
        statement = select(StockAdjustment).where(StockAdjustment.id == adjustment_id)
        statement = self._apply_tenant_filter(statement, StockAdjustment)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_number(self, adjustment_number: str) -> StockAdjustment | None:
        statement = select(StockAdjustment).where(StockAdjustment.adjustment_number == adjustment_number)
        statement = self._apply_tenant_filter(statement, StockAdjustment)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(
        self,
        statement,
        warehouse_id: str | None = None,
        product_id: str | None = None,
        reason: StockAdjustmentReason | None = None,
    ):
        if warehouse_id is not None:
            statement = statement.where(StockAdjustment.warehouse_id == warehouse_id)
        if product_id is not None:
            statement = statement.where(StockAdjustment.product_id == product_id)
        if reason is not None:
            statement = statement.where(StockAdjustment.reason == reason)
        return statement

    async def list(
        self,
        warehouse_id: str | None = None,
        product_id: str | None = None,
        reason: StockAdjustmentReason | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StockAdjustment]:
        statement = select(StockAdjustment).order_by(StockAdjustment.created_at.desc()).limit(limit).offset(offset)
        statement = self._apply_filters(statement, warehouse_id, product_id, reason)
        statement = self._apply_tenant_filter(statement, StockAdjustment)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, warehouse_id: str | None = None, product_id: str | None = None, reason: StockAdjustmentReason | None = None) -> int:
        statement = select(func.count(StockAdjustment.id))
        statement = self._apply_filters(statement, warehouse_id, product_id, reason)
        statement = self._apply_tenant_filter(statement, StockAdjustment)
        result = await self.session.execute(statement)
        return result.scalar_one()
