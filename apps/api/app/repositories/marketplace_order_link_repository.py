from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace_order_link import MarketplaceOrderLink
from app.repositories.base_repository import BaseRepository


class MarketplaceOrderLinkRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, link: MarketplaceOrderLink) -> MarketplaceOrderLink:
        self._add_tenant_on_create(link)
        self.session.add(link)
        await self.session.commit()
        await self.session.refresh(link)
        return link

    async def save(self, link: MarketplaceOrderLink) -> MarketplaceOrderLink:
        self.session.add(link)
        await self.session.commit()
        await self.session.refresh(link)
        return link

    async def get_by_id(self, link_id: str) -> MarketplaceOrderLink | None:
        statement = select(MarketplaceOrderLink).where(MarketplaceOrderLink.id == link_id)
        statement = self._apply_tenant_filter(statement, MarketplaceOrderLink)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_connector_and_external_id(self, connector_id: str, external_order_id: str) -> MarketplaceOrderLink | None:
        statement = select(MarketplaceOrderLink).where(
            MarketplaceOrderLink.marketplace_connector_id == connector_id,
            MarketplaceOrderLink.external_order_id == external_order_id,
        )
        statement = self._apply_tenant_filter(statement, MarketplaceOrderLink)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list(
        self,
        connector_id: str | None = None,
        status_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MarketplaceOrderLink]:
        statement = select(MarketplaceOrderLink).order_by(MarketplaceOrderLink.created_at.desc()).limit(limit).offset(offset)
        if connector_id is not None:
            statement = statement.where(MarketplaceOrderLink.marketplace_connector_id == connector_id)
        if status_filter is not None:
            statement = statement.where(MarketplaceOrderLink.status == status_filter)
        statement = self._apply_tenant_filter(statement, MarketplaceOrderLink)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, connector_id: str | None = None, status_filter: str | None = None) -> int:
        statement = select(func.count(MarketplaceOrderLink.id))
        if connector_id is not None:
            statement = statement.where(MarketplaceOrderLink.marketplace_connector_id == connector_id)
        if status_filter is not None:
            statement = statement.where(MarketplaceOrderLink.status == status_filter)
        statement = self._apply_tenant_filter(statement, MarketplaceOrderLink)
        result = await self.session.execute(statement)
        return result.scalar_one()
