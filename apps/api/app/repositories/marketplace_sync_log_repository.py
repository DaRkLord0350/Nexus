from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace_sync_log import MarketplaceSyncLog
from app.repositories.base_repository import BaseRepository


class MarketplaceSyncLogRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, log: MarketplaceSyncLog) -> MarketplaceSyncLog:
        self._add_tenant_on_create(log)
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def save(self, log: MarketplaceSyncLog) -> MarketplaceSyncLog:
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def get_by_id(self, log_id: str) -> MarketplaceSyncLog | None:
        statement = select(MarketplaceSyncLog).where(MarketplaceSyncLog.id == log_id)
        statement = self._apply_tenant_filter(statement, MarketplaceSyncLog)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list(
        self,
        connector_id: str | None = None,
        sync_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MarketplaceSyncLog]:
        statement = select(MarketplaceSyncLog).order_by(MarketplaceSyncLog.started_at.desc()).limit(limit).offset(offset)
        if connector_id is not None:
            statement = statement.where(MarketplaceSyncLog.marketplace_connector_id == connector_id)
        if sync_type is not None:
            statement = statement.where(MarketplaceSyncLog.sync_type == sync_type)
        statement = self._apply_tenant_filter(statement, MarketplaceSyncLog)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, connector_id: str | None = None, sync_type: str | None = None) -> int:
        statement = select(func.count(MarketplaceSyncLog.id))
        if connector_id is not None:
            statement = statement.where(MarketplaceSyncLog.marketplace_connector_id == connector_id)
        if sync_type is not None:
            statement = statement.where(MarketplaceSyncLog.sync_type == sync_type)
        statement = self._apply_tenant_filter(statement, MarketplaceSyncLog)
        result = await self.session.execute(statement)
        return result.scalar_one()
