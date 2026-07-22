from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tax_class import TaxClass
from app.repositories.base_repository import BaseRepository


class TaxClassRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, tax_class: TaxClass) -> TaxClass:
        self._add_tenant_on_create(tax_class)
        self.session.add(tax_class)
        await self.session.commit()
        await self.session.refresh(tax_class)
        return tax_class

    async def save(self, tax_class: TaxClass) -> TaxClass:
        self.session.add(tax_class)
        await self.session.commit()
        await self.session.refresh(tax_class)
        return tax_class

    async def get_by_id(self, tax_class_id: str) -> TaxClass | None:
        statement = select(TaxClass).where(TaxClass.id == tax_class_id)
        statement = self._apply_tenant_filter(statement, TaxClass)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> TaxClass | None:
        statement = select(TaxClass).where(TaxClass.code == code)
        statement = self._apply_tenant_filter(statement, TaxClass)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list(self, is_active: bool | None = None, limit: int = 100, offset: int = 0) -> list[TaxClass]:
        statement = select(TaxClass).order_by(TaxClass.name.asc()).limit(limit).offset(offset)
        if is_active is not None:
            statement = statement.where(TaxClass.is_active == is_active)
        statement = self._apply_tenant_filter(statement, TaxClass)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, is_active: bool | None = None) -> int:
        statement = select(func.count(TaxClass.id))
        if is_active is not None:
            statement = statement.where(TaxClass.is_active == is_active)
        statement = self._apply_tenant_filter(statement, TaxClass)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def unset_default(self, exclude_id: str | None = None) -> None:
        statement = update(TaxClass).where(TaxClass.is_default.is_(True)).values(is_default=False)
        if exclude_id:
            statement = statement.where(TaxClass.id != exclude_id)
        statement = self._apply_tenant_filter(statement, TaxClass)
        await self.session.execute(statement)

    async def soft_delete(self, tax_class_id: str) -> None:
        statement = update(TaxClass).where(TaxClass.id == tax_class_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, TaxClass)
        await self.session.execute(statement)
        await self.session.commit()
