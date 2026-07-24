from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace_connector import MarketplaceConnector
from app.repositories.base_repository import BaseRepository

SORTABLE_FIELDS = {
    "name": MarketplaceConnector.name,
    "created_at": MarketplaceConnector.created_at,
}


class MarketplaceConnectorRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, connector: MarketplaceConnector) -> MarketplaceConnector:
        self._add_tenant_on_create(connector)
        self.session.add(connector)
        await self.session.commit()
        await self.session.refresh(connector)
        return connector

    async def save(self, connector: MarketplaceConnector) -> MarketplaceConnector:
        self.session.add(connector)
        await self.session.commit()
        await self.session.refresh(connector)
        return connector

    async def save_no_commit(self, connector: MarketplaceConnector) -> MarketplaceConnector:
        self.session.add(connector)
        return connector

    async def get_by_id(self, connector_id: str) -> MarketplaceConnector | None:
        statement = select(MarketplaceConnector).where(MarketplaceConnector.id == connector_id)
        statement = self._apply_tenant_filter(statement, MarketplaceConnector)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> MarketplaceConnector | None:
        statement = select(MarketplaceConnector).where(MarketplaceConnector.code == code)
        statement = self._apply_tenant_filter(statement, MarketplaceConnector)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list(
        self,
        is_active: bool | None = None,
        connector_type: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[MarketplaceConnector]:
        column = SORTABLE_FIELDS.get(sort_by, MarketplaceConnector.created_at)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(MarketplaceConnector).order_by(order_clause).limit(limit).offset(offset)
        if is_active is not None:
            statement = statement.where(MarketplaceConnector.is_active == is_active)
        if connector_type is not None:
            statement = statement.where(MarketplaceConnector.connector_type == connector_type)
        statement = self._apply_tenant_filter(statement, MarketplaceConnector)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, is_active: bool | None = None, connector_type: str | None = None) -> int:
        statement = select(func.count(MarketplaceConnector.id))
        if is_active is not None:
            statement = statement.where(MarketplaceConnector.is_active == is_active)
        if connector_type is not None:
            statement = statement.where(MarketplaceConnector.connector_type == connector_type)
        statement = self._apply_tenant_filter(statement, MarketplaceConnector)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def list_all_active(self) -> list[MarketplaceConnector]:
        statement = select(MarketplaceConnector).where(MarketplaceConnector.is_active.is_(True))
        statement = self._apply_tenant_filter(statement, MarketplaceConnector)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def soft_delete(self, connector_id: str) -> None:
        statement = update(MarketplaceConnector).where(MarketplaceConnector.id == connector_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, MarketplaceConnector)
        await self.session.execute(statement)
        await self.session.commit()
