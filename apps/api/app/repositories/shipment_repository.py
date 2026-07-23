from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipment import Shipment, ShipmentStatus
from app.models.shipment_item import ShipmentItem
from app.repositories.base_repository import BaseRepository

SORTABLE_FIELDS = {
    "shipment_number": Shipment.shipment_number,
    "status": Shipment.status,
    "created_at": Shipment.created_at,
}


class ShipmentRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, shipment: Shipment) -> Shipment:
        self._add_tenant_on_create(shipment)
        self.session.add(shipment)
        await self.session.commit()
        await self.session.refresh(shipment)
        return shipment

    async def save_no_commit(self, shipment: Shipment) -> Shipment:
        self.session.add(shipment)
        await self.session.flush()
        return shipment

    async def save(self, shipment: Shipment) -> Shipment:
        self.session.add(shipment)
        await self.session.commit()
        await self.session.refresh(shipment)
        return shipment

    async def get_by_id(self, shipment_id: str) -> Shipment | None:
        statement = select(Shipment).where(Shipment.id == shipment_id)
        statement = self._apply_tenant_filter(statement, Shipment)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_number(self, shipment_number: str) -> Shipment | None:
        statement = select(Shipment).where(Shipment.shipment_number == shipment_number)
        statement = self._apply_tenant_filter(statement, Shipment)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_pickup(self, pickup_id: str) -> list[Shipment]:
        statement = select(Shipment).where(Shipment.pickup_id == pickup_id)
        statement = self._apply_tenant_filter(statement, Shipment)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_tracking_number(self, tracking_number: str) -> Shipment | None:
        statement = select(Shipment).where(Shipment.tracking_number == tracking_number)
        statement = self._apply_tenant_filter(statement, Shipment)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(
        self,
        statement,
        order_id: str | None = None,
        warehouse_id: str | None = None,
        shipping_provider_id: str | None = None,
        status: ShipmentStatus | None = None,
        q: str | None = None,
    ):
        if order_id is not None:
            statement = statement.where(Shipment.order_id == order_id)
        if warehouse_id is not None:
            statement = statement.where(Shipment.warehouse_id == warehouse_id)
        if shipping_provider_id is not None:
            statement = statement.where(Shipment.shipping_provider_id == shipping_provider_id)
        if status is not None:
            statement = statement.where(Shipment.status == status)
        if q:
            like = f"%{q}%"
            statement = statement.where(or_(Shipment.shipment_number.ilike(like), Shipment.tracking_number.ilike(like)))
        return statement

    async def list(
        self,
        order_id: str | None = None,
        warehouse_id: str | None = None,
        shipping_provider_id: str | None = None,
        status: ShipmentStatus | None = None,
        q: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Shipment]:
        column = SORTABLE_FIELDS.get(sort_by, Shipment.created_at)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(Shipment).order_by(order_clause).limit(limit).offset(offset)
        statement = self._apply_filters(statement, order_id, warehouse_id, shipping_provider_id, status, q)
        statement = self._apply_tenant_filter(statement, Shipment)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(
        self,
        order_id: str | None = None,
        warehouse_id: str | None = None,
        shipping_provider_id: str | None = None,
        status: ShipmentStatus | None = None,
        q: str | None = None,
    ) -> int:
        statement = select(func.count(Shipment.id))
        statement = self._apply_filters(statement, order_id, warehouse_id, shipping_provider_id, status, q)
        statement = self._apply_tenant_filter(statement, Shipment)
        result = await self.session.execute(statement)
        return result.scalar_one()


class ShipmentItemRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create_no_commit(self, item: ShipmentItem) -> ShipmentItem:
        self._add_tenant_on_create(item)
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_for_shipment(self, shipment_id: str) -> list[ShipmentItem]:
        statement = select(ShipmentItem).where(ShipmentItem.shipment_id == shipment_id).order_by(ShipmentItem.created_at.asc())
        statement = self._apply_tenant_filter(statement, ShipmentItem)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def sum_shipped_for_order_item(self, order_item_id: str) -> int:
        statement = select(func.coalesce(func.sum(ShipmentItem.quantity), 0)).where(ShipmentItem.order_item_id == order_item_id)
        statement = self._apply_tenant_filter(statement, ShipmentItem)
        result = await self.session.execute(statement)
        return result.scalar_one()
