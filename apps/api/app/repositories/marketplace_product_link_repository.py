from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace_product_link import MarketplaceProductLink
from app.repositories.base_repository import BaseRepository


class MarketplaceProductLinkRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, link: MarketplaceProductLink) -> MarketplaceProductLink:
        self._add_tenant_on_create(link)
        self.session.add(link)
        await self.session.commit()
        await self.session.refresh(link)
        return link

    async def save(self, link: MarketplaceProductLink) -> MarketplaceProductLink:
        self.session.add(link)
        await self.session.commit()
        await self.session.refresh(link)
        return link

    async def get_by_id(self, link_id: str) -> MarketplaceProductLink | None:
        statement = select(MarketplaceProductLink).where(MarketplaceProductLink.id == link_id)
        statement = self._apply_tenant_filter(statement, MarketplaceProductLink)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_connector_and_product(self, connector_id: str, product_id: str) -> MarketplaceProductLink | None:
        statement = select(MarketplaceProductLink).where(
            MarketplaceProductLink.marketplace_connector_id == connector_id,
            MarketplaceProductLink.product_id == product_id,
        )
        statement = self._apply_tenant_filter(statement, MarketplaceProductLink)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list(
        self,
        connector_id: str | None = None,
        sync_status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MarketplaceProductLink]:
        statement = select(MarketplaceProductLink).order_by(MarketplaceProductLink.created_at.desc()).limit(limit).offset(offset)
        if connector_id is not None:
            statement = statement.where(MarketplaceProductLink.marketplace_connector_id == connector_id)
        if sync_status is not None:
            statement = statement.where(MarketplaceProductLink.sync_status == sync_status)
        statement = self._apply_tenant_filter(statement, MarketplaceProductLink)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, connector_id: str | None = None, sync_status: str | None = None) -> int:
        statement = select(func.count(MarketplaceProductLink.id))
        if connector_id is not None:
            statement = statement.where(MarketplaceProductLink.marketplace_connector_id == connector_id)
        if sync_status is not None:
            statement = statement.where(MarketplaceProductLink.sync_status == sync_status)
        statement = self._apply_tenant_filter(statement, MarketplaceProductLink)
        result = await self.session.execute(statement)
        return result.scalar_one()
