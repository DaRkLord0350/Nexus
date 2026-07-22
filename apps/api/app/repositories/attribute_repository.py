from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attribute import Attribute
from app.repositories.base_repository import BaseRepository

SORTABLE_FIELDS = {
    "name": Attribute.name,
    "sort_order": Attribute.sort_order,
    "created_at": Attribute.created_at,
}


class AttributeRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, attribute: Attribute) -> Attribute:
        self._add_tenant_on_create(attribute)
        self.session.add(attribute)
        await self.session.commit()
        await self.session.refresh(attribute)
        return attribute

    async def save(self, attribute: Attribute) -> Attribute:
        self.session.add(attribute)
        await self.session.commit()
        await self.session.refresh(attribute)
        return attribute

    async def get_by_id(self, attribute_id: str) -> Attribute | None:
        statement = select(Attribute).where(Attribute.id == attribute_id)
        statement = self._apply_tenant_filter(statement, Attribute)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Attribute | None:
        statement = select(Attribute).where(Attribute.code == code)
        statement = self._apply_tenant_filter(statement, Attribute)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(self, statement, is_active: bool | None = None, is_variant_attribute: bool | None = None, q: str | None = None):
        if is_active is not None:
            statement = statement.where(Attribute.is_active == is_active)
        if is_variant_attribute is not None:
            statement = statement.where(Attribute.is_variant_attribute == is_variant_attribute)
        if q:
            like = f"%{q}%"
            statement = statement.where(or_(Attribute.name.ilike(like), Attribute.code.ilike(like)))
        return statement

    async def list(
        self,
        is_active: bool | None = None,
        is_variant_attribute: bool | None = None,
        q: str | None = None,
        sort_by: str = "sort_order",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Attribute]:
        column = SORTABLE_FIELDS.get(sort_by, Attribute.sort_order)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(Attribute).order_by(order_clause).limit(limit).offset(offset)
        statement = self._apply_filters(statement, is_active, is_variant_attribute, q)
        statement = self._apply_tenant_filter(statement, Attribute)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, is_active: bool | None = None, is_variant_attribute: bool | None = None, q: str | None = None) -> int:
        statement = select(func.count(Attribute.id))
        statement = self._apply_filters(statement, is_active, is_variant_attribute, q)
        statement = self._apply_tenant_filter(statement, Attribute)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def soft_delete(self, attribute_id: str) -> None:
        statement = update(Attribute).where(Attribute.id == attribute_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Attribute)
        await self.session.execute(statement)
        await self.session.commit()

    async def bulk_soft_delete(self, attribute_ids: list[str]) -> int:
        if not attribute_ids:
            return 0
        statement = update(Attribute).where(Attribute.id.in_(attribute_ids)).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Attribute)
        result = await self.session.execute(statement)
        await self.session.commit()
        return result.rowcount or 0
