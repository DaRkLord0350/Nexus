from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipment_tracking import ShipmentTracking
from app.repositories.base_repository import BaseRepository


class ShipmentTrackingRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, event: ShipmentTracking) -> ShipmentTracking:
        self._add_tenant_on_create(event)
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def list_for_shipment(self, shipment_id: str) -> list[ShipmentTracking]:
        statement = select(ShipmentTracking).where(ShipmentTracking.shipment_id == shipment_id).order_by(ShipmentTracking.occurred_at.asc())
        statement = self._apply_tenant_filter(statement, ShipmentTracking)
        result = await self.session.execute(statement)
        return result.scalars().all()
