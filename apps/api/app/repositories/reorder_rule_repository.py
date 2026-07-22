from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reorder_rule import ReorderRule
from app.repositories.base_repository import BaseRepository


class ReorderRuleRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, rule: ReorderRule) -> ReorderRule:
        self._add_tenant_on_create(rule)
        self.session.add(rule)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def save(self, rule: ReorderRule) -> ReorderRule:
        self.session.add(rule)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def save_no_commit(self, rule: ReorderRule) -> ReorderRule:
        self.session.add(rule)
        await self.session.flush()
        return rule

    async def get_by_id(self, rule_id: str) -> ReorderRule | None:
        statement = select(ReorderRule).where(ReorderRule.id == rule_id)
        statement = self._apply_tenant_filter(statement, ReorderRule)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_grain(self, product_id: str, variant_id: str | None, warehouse_id: str) -> ReorderRule | None:
        statement = select(ReorderRule).where(
            ReorderRule.product_id == product_id,
            ReorderRule.variant_id == variant_id,
            ReorderRule.warehouse_id == warehouse_id,
        )
        statement = self._apply_tenant_filter(statement, ReorderRule)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(self, statement, warehouse_id: str | None = None, product_id: str | None = None, is_active: bool | None = None):
        if warehouse_id is not None:
            statement = statement.where(ReorderRule.warehouse_id == warehouse_id)
        if product_id is not None:
            statement = statement.where(ReorderRule.product_id == product_id)
        if is_active is not None:
            statement = statement.where(ReorderRule.is_active == is_active)
        return statement

    async def list(
        self,
        warehouse_id: str | None = None,
        product_id: str | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReorderRule]:
        statement = select(ReorderRule).order_by(ReorderRule.created_at.desc()).limit(limit).offset(offset)
        statement = self._apply_filters(statement, warehouse_id, product_id, is_active)
        statement = self._apply_tenant_filter(statement, ReorderRule)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, warehouse_id: str | None = None, product_id: str | None = None, is_active: bool | None = None) -> int:
        statement = select(func.count(ReorderRule.id))
        statement = self._apply_filters(statement, warehouse_id, product_id, is_active)
        statement = self._apply_tenant_filter(statement, ReorderRule)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def soft_delete(self, rule_id: str) -> None:
        statement = update(ReorderRule).where(ReorderRule.id == rule_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, ReorderRule)
        await self.session.execute(statement)
        await self.session.commit()
