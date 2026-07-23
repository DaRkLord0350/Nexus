from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.return_shipment import ReturnShipment, ReturnShipmentStatus
from app.repositories.base_repository import BaseRepository

SORTABLE_FIELDS = {
    "return_shipment_number": ReturnShipment.return_shipment_number,
    "status": ReturnShipment.status,
    "created_at": ReturnShipment.created_at,
}


class ReturnShipmentRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, return_shipment: ReturnShipment) -> ReturnShipment:
        self._add_tenant_on_create(return_shipment)
        self.session.add(return_shipment)
        await self.session.commit()
        await self.session.refresh(return_shipment)
        return return_shipment

    async def save(self, return_shipment: ReturnShipment) -> ReturnShipment:
        self.session.add(return_shipment)
        await self.session.commit()
        await self.session.refresh(return_shipment)
        return return_shipment

    async def get_by_id(self, return_shipment_id: str) -> ReturnShipment | None:
        statement = select(ReturnShipment).where(ReturnShipment.id == return_shipment_id)
        statement = self._apply_tenant_filter(statement, ReturnShipment)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_number(self, return_shipment_number: str) -> ReturnShipment | None:
        statement = select(ReturnShipment).where(ReturnShipment.return_shipment_number == return_shipment_number)
        statement = self._apply_tenant_filter(statement, ReturnShipment)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_for_return_request(self, return_request_id: str) -> ReturnShipment | None:
        statement = select(ReturnShipment).where(ReturnShipment.return_request_id == return_request_id)
        statement = self._apply_tenant_filter(statement, ReturnShipment)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(self, statement, warehouse_id: str | None = None, status: ReturnShipmentStatus | None = None):
        if warehouse_id is not None:
            statement = statement.where(ReturnShipment.warehouse_id == warehouse_id)
        if status is not None:
            statement = statement.where(ReturnShipment.status == status)
        return statement

    async def list(
        self,
        warehouse_id: str | None = None,
        status: ReturnShipmentStatus | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReturnShipment]:
        column = SORTABLE_FIELDS.get(sort_by, ReturnShipment.created_at)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(ReturnShipment).order_by(order_clause).limit(limit).offset(offset)
        statement = self._apply_filters(statement, warehouse_id, status)
        statement = self._apply_tenant_filter(statement, ReturnShipment)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, warehouse_id: str | None = None, status: ReturnShipmentStatus | None = None) -> int:
        statement = select(func.count(ReturnShipment.id))
        statement = self._apply_filters(statement, warehouse_id, status)
        statement = self._apply_tenant_filter(statement, ReturnShipment)
        result = await self.session.execute(statement)
        return result.scalar_one()
