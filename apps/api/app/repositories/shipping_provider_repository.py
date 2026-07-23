from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipping_provider import ShippingProvider
from app.repositories.base_repository import BaseRepository

SORTABLE_FIELDS = {
    "name": ShippingProvider.name,
    "priority": ShippingProvider.priority,
    "created_at": ShippingProvider.created_at,
}


class ShippingProviderRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, provider: ShippingProvider) -> ShippingProvider:
        self._add_tenant_on_create(provider)
        self.session.add(provider)
        await self.session.commit()
        await self.session.refresh(provider)
        return provider

    async def save(self, provider: ShippingProvider) -> ShippingProvider:
        self.session.add(provider)
        await self.session.commit()
        await self.session.refresh(provider)
        return provider

    async def get_by_id(self, provider_id: str) -> ShippingProvider | None:
        statement = select(ShippingProvider).where(ShippingProvider.id == provider_id)
        statement = self._apply_tenant_filter(statement, ShippingProvider)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> ShippingProvider | None:
        statement = select(ShippingProvider).where(ShippingProvider.code == code)
        statement = self._apply_tenant_filter(statement, ShippingProvider)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_default(self) -> ShippingProvider | None:
        statement = select(ShippingProvider).where(ShippingProvider.is_default.is_(True), ShippingProvider.is_active.is_(True))
        statement = self._apply_tenant_filter(statement, ShippingProvider)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def unset_default(self, exclude_id: str | None = None) -> None:
        statement = update(ShippingProvider).where(ShippingProvider.is_default.is_(True)).values(is_default=False)
        if exclude_id:
            statement = statement.where(ShippingProvider.id != exclude_id)
        statement = self._apply_tenant_filter(statement, ShippingProvider)
        await self.session.execute(statement)
        await self.session.commit()

    async def list(
        self,
        is_active: bool | None = None,
        provider_type: str | None = None,
        sort_by: str = "priority",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[ShippingProvider]:
        column = SORTABLE_FIELDS.get(sort_by, ShippingProvider.priority)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(ShippingProvider).order_by(order_clause).limit(limit).offset(offset)
        if is_active is not None:
            statement = statement.where(ShippingProvider.is_active == is_active)
        if provider_type is not None:
            statement = statement.where(ShippingProvider.provider_type == provider_type)
        statement = self._apply_tenant_filter(statement, ShippingProvider)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, is_active: bool | None = None, provider_type: str | None = None) -> int:
        statement = select(func.count(ShippingProvider.id))
        if is_active is not None:
            statement = statement.where(ShippingProvider.is_active == is_active)
        if provider_type is not None:
            statement = statement.where(ShippingProvider.provider_type == provider_type)
        statement = self._apply_tenant_filter(statement, ShippingProvider)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def soft_delete(self, provider_id: str) -> None:
        statement = update(ShippingProvider).where(ShippingProvider.id == provider_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, ShippingProvider)
        await self.session.execute(statement)
        await self.session.commit()
