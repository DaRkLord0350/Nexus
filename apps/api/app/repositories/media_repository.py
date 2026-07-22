from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete as sa_delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import Media
from app.repositories.base_repository import BaseRepository


class MediaRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, media: Media) -> Media:
        self._add_tenant_on_create(media)
        self.session.add(media)
        await self.session.commit()
        await self.session.refresh(media)
        return media

    async def save(self, media: Media) -> Media:
        self.session.add(media)
        await self.session.commit()
        await self.session.refresh(media)
        return media

    async def get_by_id(self, media_id: str) -> Media | None:
        statement = select(Media).where(Media.id == media_id)
        statement = self._apply_tenant_filter(statement, Media)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_product(self, product_id: str) -> list[Media]:
        statement = select(Media).where(Media.product_id == product_id).order_by(Media.sort_order.asc(), Media.created_at.asc())
        statement = self._apply_tenant_filter(statement, Media)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def list_for_variant(self, variant_id: str) -> list[Media]:
        statement = select(Media).where(Media.variant_id == variant_id).order_by(Media.sort_order.asc(), Media.created_at.asc())
        statement = self._apply_tenant_filter(statement, Media)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def unset_primary_for_product(self, product_id: str, exclude_media_id: str | None = None) -> None:
        statement = update(Media).where(Media.product_id == product_id, Media.is_primary.is_(True)).values(is_primary=False)
        if exclude_media_id:
            statement = statement.where(Media.id != exclude_media_id)
        statement = self._apply_tenant_filter(statement, Media)
        await self.session.execute(statement)

    async def delete(self, media_id: str) -> None:
        statement = sa_delete(Media).where(Media.id == media_id)
        statement = self._apply_tenant_filter(statement, Media)
        await self.session.execute(statement)
        await self.session.commit()

    async def bulk_delete(self, media_ids: list[str]) -> int:
        if not media_ids:
            return 0
        statement = sa_delete(Media).where(Media.id.in_(media_ids))
        statement = self._apply_tenant_filter(statement, Media)
        result = await self.session.execute(statement)
        await self.session.commit()
        return result.rowcount or 0

    async def reorder(self, media_id: str, sort_order: int) -> None:
        statement = update(Media).where(Media.id == media_id).values(sort_order=sort_order)
        statement = self._apply_tenant_filter(statement, Media)
        await self.session.execute(statement)
