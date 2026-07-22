from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand import Brand, BrandStatus
from app.repositories.base_repository import BaseRepository

SORTABLE_FIELDS = {
    "name": Brand.name,
    "created_at": Brand.created_at,
    "updated_at": Brand.updated_at,
}


class BrandRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, brand: Brand) -> Brand:
        self._add_tenant_on_create(brand)
        self.session.add(brand)
        await self.session.commit()
        await self.session.refresh(brand)
        return brand

    async def save(self, brand: Brand) -> Brand:
        self.session.add(brand)
        await self.session.commit()
        await self.session.refresh(brand)
        return brand

    async def get_by_id(self, brand_id: str) -> Brand | None:
        statement = select(Brand).where(Brand.id == brand_id)
        statement = self._apply_tenant_filter(statement, Brand)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Brand | None:
        statement = select(Brand).where(Brand.slug == slug)
        statement = self._apply_tenant_filter(statement, Brand)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(self, statement, status: BrandStatus | None = None, is_featured: bool | None = None, q: str | None = None):
        if status is not None:
            statement = statement.where(Brand.status == status)
        if is_featured is not None:
            statement = statement.where(Brand.is_featured == is_featured)
        if q:
            like = f"%{q}%"
            statement = statement.where(or_(Brand.name.ilike(like), Brand.slug.ilike(like)))
        return statement

    async def list(
        self,
        status: BrandStatus | None = None,
        is_featured: bool | None = None,
        q: str | None = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Brand]:
        column = SORTABLE_FIELDS.get(sort_by, Brand.name)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(Brand).order_by(order_clause).limit(limit).offset(offset)
        statement = self._apply_filters(statement, status, is_featured, q)
        statement = self._apply_tenant_filter(statement, Brand)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, status: BrandStatus | None = None, is_featured: bool | None = None, q: str | None = None) -> int:
        statement = select(func.count(Brand.id))
        statement = self._apply_filters(statement, status, is_featured, q)
        statement = self._apply_tenant_filter(statement, Brand)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def get_by_id_including_deleted(self, brand_id: str) -> Brand | None:
        statement = select(Brand).where(Brand.id == brand_id)
        if not self.is_superuser and self.organization_id is not None:
            statement = statement.where(Brand.organization_id == self.organization_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def soft_delete(self, brand_id: str) -> None:
        statement = update(Brand).where(Brand.id == brand_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Brand)
        await self.session.execute(statement)
        await self.session.commit()

    async def restore(self, brand_id: str) -> Brand | None:
        statement = update(Brand).where(Brand.id == brand_id).values(deleted_at=None)
        if not self.is_superuser and self.organization_id is not None:
            statement = statement.where(Brand.organization_id == self.organization_id)
        await self.session.execute(statement)
        await self.session.commit()
        return await self.get_by_id(brand_id)

    async def bulk_soft_delete(self, brand_ids: list[str]) -> int:
        if not brand_ids:
            return 0
        statement = update(Brand).where(Brand.id.in_(brand_ids)).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Brand)
        result = await self.session.execute(statement)
        await self.session.commit()
        return result.rowcount or 0
