from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wishlist import Wishlist
from app.repositories.base_repository import BaseRepository


class WishlistRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, item: Wishlist) -> Wishlist:
        self._add_tenant_on_create(item)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def get_by_id(self, item_id: str) -> Wishlist | None:
        statement = select(Wishlist).where(Wishlist.id == item_id)
        statement = self._apply_tenant_filter(statement, Wishlist)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_existing(self, customer_id: str, product_id: str, variant_id: str | None) -> Wishlist | None:
        statement = select(Wishlist).where(
            Wishlist.customer_id == customer_id, Wishlist.product_id == product_id, Wishlist.variant_id == variant_id,
        )
        statement = self._apply_tenant_filter(statement, Wishlist)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_customer(self, customer_id: str, limit: int = 50, offset: int = 0) -> list[Wishlist]:
        statement = (
            select(Wishlist).where(Wishlist.customer_id == customer_id)
            .order_by(Wishlist.created_at.desc()).limit(limit).offset(offset)
        )
        statement = self._apply_tenant_filter(statement, Wishlist)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count_for_customer(self, customer_id: str) -> int:
        statement = select(func.count(Wishlist.id)).where(Wishlist.customer_id == customer_id)
        statement = self._apply_tenant_filter(statement, Wishlist)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def delete(self, item_id: str) -> None:
        statement = select(Wishlist).where(Wishlist.id == item_id)
        statement = self._apply_tenant_filter(statement, Wishlist)
        result = await self.session.execute(statement)
        item = result.scalar_one_or_none()
        if item:
            await self.session.delete(item)
            await self.session.commit()
