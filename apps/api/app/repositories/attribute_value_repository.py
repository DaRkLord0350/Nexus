from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attribute_value import AttributeValue
from app.repositories.base_repository import BaseRepository


class AttributeValueRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, value: AttributeValue) -> AttributeValue:
        self._add_tenant_on_create(value)
        self.session.add(value)
        await self.session.commit()
        await self.session.refresh(value)
        return value

    async def save(self, value: AttributeValue) -> AttributeValue:
        self.session.add(value)
        await self.session.commit()
        await self.session.refresh(value)
        return value

    async def get_by_id(self, value_id: str) -> AttributeValue | None:
        statement = select(AttributeValue).where(AttributeValue.id == value_id)
        statement = self._apply_tenant_filter(statement, AttributeValue)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_slug(self, attribute_id: str, slug: str) -> AttributeValue | None:
        statement = select(AttributeValue).where(AttributeValue.attribute_id == attribute_id, AttributeValue.slug == slug)
        statement = self._apply_tenant_filter(statement, AttributeValue)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_attribute(self, attribute_id: str, is_active: bool | None = None) -> list[AttributeValue]:
        statement = select(AttributeValue).where(AttributeValue.attribute_id == attribute_id).order_by(AttributeValue.sort_order.asc(), AttributeValue.value.asc())
        if is_active is not None:
            statement = statement.where(AttributeValue.is_active == is_active)
        statement = self._apply_tenant_filter(statement, AttributeValue)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def list_by_ids(self, value_ids: list[str]) -> list[AttributeValue]:
        if not value_ids:
            return []
        statement = select(AttributeValue).where(AttributeValue.id.in_(value_ids))
        statement = self._apply_tenant_filter(statement, AttributeValue)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count_for_attribute(self, attribute_id: str) -> int:
        statement = select(func.count(AttributeValue.id)).where(AttributeValue.attribute_id == attribute_id)
        statement = self._apply_tenant_filter(statement, AttributeValue)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def soft_delete(self, value_id: str) -> None:
        statement = update(AttributeValue).where(AttributeValue.id == value_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, AttributeValue)
        await self.session.execute(statement)
        await self.session.commit()

    async def soft_delete_for_attribute(self, attribute_id: str) -> None:
        statement = update(AttributeValue).where(AttributeValue.attribute_id == attribute_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, AttributeValue)
        await self.session.execute(statement)
        await self.session.commit()

    async def bulk_soft_delete(self, value_ids: list[str]) -> int:
        if not value_ids:
            return 0
        statement = update(AttributeValue).where(AttributeValue.id.in_(value_ids)).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, AttributeValue)
        result = await self.session.execute(statement)
        await self.session.commit()
        return result.rowcount or 0
