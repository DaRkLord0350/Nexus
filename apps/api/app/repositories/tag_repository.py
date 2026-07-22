from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete as sa_delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_tag import ProductTag
from app.models.tag import Tag
from app.repositories.base_repository import BaseRepository


class TagRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, tag: Tag) -> Tag:
        self._add_tenant_on_create(tag)
        self.session.add(tag)
        await self.session.commit()
        await self.session.refresh(tag)
        return tag

    async def save(self, tag: Tag) -> Tag:
        self.session.add(tag)
        await self.session.commit()
        await self.session.refresh(tag)
        return tag

    async def get_by_id(self, tag_id: str) -> Tag | None:
        statement = select(Tag).where(Tag.id == tag_id)
        statement = self._apply_tenant_filter(statement, Tag)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Tag | None:
        statement = select(Tag).where(Tag.slug == slug)
        statement = self._apply_tenant_filter(statement, Tag)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_ids(self, tag_ids: list[str]) -> list[Tag]:
        if not tag_ids:
            return []
        statement = select(Tag).where(Tag.id.in_(tag_ids))
        statement = self._apply_tenant_filter(statement, Tag)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def list(self, q: str | None = None, limit: int = 100, offset: int = 0) -> list[Tag]:
        statement = select(Tag).order_by(Tag.name.asc()).limit(limit).offset(offset)
        if q:
            statement = statement.where(Tag.name.ilike(f"%{q}%"))
        statement = self._apply_tenant_filter(statement, Tag)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, q: str | None = None) -> int:
        statement = select(func.count(Tag.id))
        if q:
            statement = statement.where(Tag.name.ilike(f"%{q}%"))
        statement = self._apply_tenant_filter(statement, Tag)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def count_products_for_tag(self, tag_id: str) -> int:
        statement = select(func.count(ProductTag.id)).where(ProductTag.tag_id == tag_id)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def soft_delete(self, tag_id: str) -> None:
        statement = update(Tag).where(Tag.id == tag_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Tag)
        await self.session.execute(statement)
        await self.session.commit()

    # ------------------------------------------------------------------
    # Product <-> Tag links
    # ------------------------------------------------------------------
    async def set_product_tags(self, product_id: str, tag_ids: list[str]) -> None:
        await self.session.execute(sa_delete(ProductTag).where(ProductTag.product_id == product_id))
        for tag_id in tag_ids:
            link = ProductTag(product_id=product_id, tag_id=tag_id)
            self._add_tenant_on_create(link)
            self.session.add(link)
        await self.session.commit()

    async def get_tags_for_product(self, product_id: str) -> list[Tag]:
        statement = select(Tag).join(ProductTag, ProductTag.tag_id == Tag.id).where(ProductTag.product_id == product_id)
        statement = self._apply_tenant_filter(statement, Tag)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_tags_for_products(self, product_ids: list[str]) -> dict[str, list[Tag]]:
        if not product_ids:
            return {}
        statement = (
            select(ProductTag.product_id, Tag)
            .join(Tag, ProductTag.tag_id == Tag.id)
            .where(ProductTag.product_id.in_(product_ids))
        )
        result = await self.session.execute(statement)
        grouped: dict[str, list[Tag]] = {product_id: [] for product_id in product_ids}
        for product_id, tag in result.all():
            grouped[product_id].append(tag)
        return grouped
