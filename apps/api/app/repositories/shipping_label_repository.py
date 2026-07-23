from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipping_label import ShippingLabel
from app.repositories.base_repository import BaseRepository


class ShippingLabelRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, label: ShippingLabel) -> ShippingLabel:
        self._add_tenant_on_create(label)
        self.session.add(label)
        await self.session.commit()
        await self.session.refresh(label)
        return label

    async def list_for_shipment(self, shipment_id: str) -> list[ShippingLabel]:
        statement = select(ShippingLabel).where(ShippingLabel.shipment_id == shipment_id).order_by(ShippingLabel.generated_at.desc())
        statement = self._apply_tenant_filter(statement, ShippingLabel)
        result = await self.session.execute(statement)
        return result.scalars().all()
