from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipping_rule import ShippingRule
from app.repositories.base_repository import BaseRepository


class ShippingRuleRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, rule: ShippingRule) -> ShippingRule:
        self._add_tenant_on_create(rule)
        self.session.add(rule)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def save(self, rule: ShippingRule) -> ShippingRule:
        self.session.add(rule)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def get_by_id(self, rule_id: str) -> ShippingRule | None:
        statement = select(ShippingRule).where(ShippingRule.id == rule_id)
        statement = self._apply_tenant_filter(statement, ShippingRule)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list(self, is_active: bool | None = None, limit: int = 100, offset: int = 0) -> list[ShippingRule]:
        statement = select(ShippingRule).order_by(ShippingRule.priority.asc()).limit(limit).offset(offset)
        if is_active is not None:
            statement = statement.where(ShippingRule.is_active == is_active)
        statement = self._apply_tenant_filter(statement, ShippingRule)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, is_active: bool | None = None) -> int:
        statement = select(func.count(ShippingRule.id))
        if is_active is not None:
            statement = statement.where(ShippingRule.is_active == is_active)
        statement = self._apply_tenant_filter(statement, ShippingRule)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def list_active_sorted(self) -> list[ShippingRule]:
        return await self.list(is_active=True, limit=1000)

    async def soft_delete(self, rule_id: str) -> None:
        statement = update(ShippingRule).where(ShippingRule.id == rule_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, ShippingRule)
        await self.session.execute(statement)
        await self.session.commit()
