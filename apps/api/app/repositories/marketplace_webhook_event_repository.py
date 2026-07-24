from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace_webhook_event import MarketplaceWebhookEvent, MarketplaceWebhookStatus
from app.repositories.base_repository import BaseRepository


class MarketplaceWebhookEventRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, event: MarketplaceWebhookEvent) -> MarketplaceWebhookEvent:
        self._add_tenant_on_create(event)
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def save(self, event: MarketplaceWebhookEvent) -> MarketplaceWebhookEvent:
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def get_by_id(self, event_id: str) -> MarketplaceWebhookEvent | None:
        statement = select(MarketplaceWebhookEvent).where(MarketplaceWebhookEvent.id == event_id)
        statement = self._apply_tenant_filter(statement, MarketplaceWebhookEvent)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list(
        self,
        connector_id: str | None = None,
        status_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MarketplaceWebhookEvent]:
        statement = select(MarketplaceWebhookEvent).order_by(MarketplaceWebhookEvent.received_at.desc()).limit(limit).offset(offset)
        if connector_id is not None:
            statement = statement.where(MarketplaceWebhookEvent.marketplace_connector_id == connector_id)
        if status_filter is not None:
            statement = statement.where(MarketplaceWebhookEvent.status == status_filter)
        statement = self._apply_tenant_filter(statement, MarketplaceWebhookEvent)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, connector_id: str | None = None, status_filter: str | None = None) -> int:
        statement = select(func.count(MarketplaceWebhookEvent.id))
        if connector_id is not None:
            statement = statement.where(MarketplaceWebhookEvent.marketplace_connector_id == connector_id)
        if status_filter is not None:
            statement = statement.where(MarketplaceWebhookEvent.status == status_filter)
        statement = self._apply_tenant_filter(statement, MarketplaceWebhookEvent)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def list_due_for_retry(self, limit: int = 100) -> list[MarketplaceWebhookEvent]:
        statement = select(MarketplaceWebhookEvent).where(
            MarketplaceWebhookEvent.status == MarketplaceWebhookStatus.failed,
            MarketplaceWebhookEvent.next_retry_at.is_not(None),
            MarketplaceWebhookEvent.next_retry_at <= datetime.utcnow(),
        ).order_by(MarketplaceWebhookEvent.next_retry_at.asc()).limit(limit)
        statement = self._apply_tenant_filter(statement, MarketplaceWebhookEvent)
        result = await self.session.execute(statement)
        return result.scalars().all()
