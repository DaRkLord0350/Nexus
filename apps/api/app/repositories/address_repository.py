from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address
from app.repositories.base_repository import BaseRepository


class AddressRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, address: Address) -> Address:
        self._add_tenant_on_create(address)
        self.session.add(address)
        await self.session.commit()
        await self.session.refresh(address)
        return address

    async def save(self, address: Address) -> Address:
        self.session.add(address)
        await self.session.commit()
        await self.session.refresh(address)
        return address

    async def get_by_id(self, address_id: str) -> Address | None:
        statement = select(Address).where(Address.id == address_id)
        statement = self._apply_tenant_filter(statement, Address)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_customer(self, customer_id: str, limit: int = 50, offset: int = 0) -> list[Address]:
        statement = (
            select(Address)
            .where(Address.customer_id == customer_id)
            .order_by(Address.is_default.desc(), Address.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        statement = self._apply_tenant_filter(statement, Address)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count_for_customer(self, customer_id: str) -> int:
        statement = select(Address).where(Address.customer_id == customer_id)
        statement = self._apply_tenant_filter(statement, Address)
        result = await self.session.execute(statement)
        return len(result.scalars().all())

    async def clear_default_for_customer(self, customer_id: str, address_type) -> None:
        statement = (
            update(Address)
            .where(Address.customer_id == customer_id, Address.address_type == address_type, Address.is_default.is_(True))
            .values(is_default=False)
        )
        statement = self._apply_tenant_filter(statement, Address)
        await self.session.execute(statement)
        await self.session.commit()

    async def soft_delete(self, address_id: str) -> None:
        statement = update(Address).where(Address.id == address_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Address)
        await self.session.execute(statement)
        await self.session.commit()
