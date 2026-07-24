import json

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace_connector import MarketplaceConnector
from app.repositories.marketplace_connector_repository import MarketplaceConnectorRepository


class MarketplaceConnectorService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = MarketplaceConnectorRepository(session, organization_id, is_superuser)

    async def _ensure_unique_code(self, code: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_code(code)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A marketplace connector with that code already exists.")

    async def create_connector(self, data, created_by: str | None = None) -> MarketplaceConnector:
        await self._ensure_unique_code(data.code)

        connector = MarketplaceConnector(
            name=data.name,
            code=data.code,
            connector_type=data.connector_type,
            is_active=data.is_active,
            credentials=json.dumps(data.credentials) if data.credentials else None,
            webhook_secret=data.webhook_secret,
            store_url=data.store_url,
            auto_sync_products=data.auto_sync_products,
            auto_sync_orders=data.auto_sync_orders,
            auto_sync_inventory=data.auto_sync_inventory,
            auto_sync_prices=data.auto_sync_prices,
            sync_interval_minutes=data.sync_interval_minutes,
            created_by=created_by,
        )
        return await self.repo.create(connector)

    async def _get_or_404(self, connector_id: str) -> MarketplaceConnector:
        connector = await self.repo.get_by_id(connector_id)
        if not connector:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marketplace connector not found.")
        return connector

    async def get_connector(self, connector_id: str) -> MarketplaceConnector | None:
        return await self.repo.get_by_id(connector_id)

    async def update_connector(self, connector_id: str, data) -> MarketplaceConnector:
        connector = await self._get_or_404(connector_id)
        changes = data.model_dump(exclude_unset=True)

        if "credentials" in changes:
            changes["credentials"] = json.dumps(changes["credentials"]) if changes["credentials"] else None

        for field, value in changes.items():
            setattr(connector, field, value)

        return await self.repo.save(connector)

    async def delete_connector(self, connector_id: str) -> None:
        await self._get_or_404(connector_id)
        await self.repo.soft_delete(connector_id)

    async def list_connectors(
        self,
        is_active: bool | None = None,
        connector_type: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[MarketplaceConnector], int]:
        items = await self.repo.list(is_active, connector_type, sort_by, sort_order, limit, offset)
        total = await self.repo.count(is_active, connector_type)
        return items, total
