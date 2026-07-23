from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.return_request import ReturnStatus
from app.models.return_shipment import ReturnShipment, ReturnShipmentStatus
from app.repositories.order_repository import OrderRepository
from app.repositories.return_request_repository import ReturnRequestRepository
from app.repositories.return_shipment_repository import ReturnShipmentRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.services.return_service import ReturnService

ALLOWED_TRANSITIONS: dict[ReturnShipmentStatus, set[ReturnShipmentStatus]] = {
    ReturnShipmentStatus.pending: {ReturnShipmentStatus.label_generated, ReturnShipmentStatus.cancelled},
    ReturnShipmentStatus.label_generated: {ReturnShipmentStatus.reverse_pickup_scheduled, ReturnShipmentStatus.cancelled},
    ReturnShipmentStatus.reverse_pickup_scheduled: {ReturnShipmentStatus.in_transit, ReturnShipmentStatus.cancelled},
    ReturnShipmentStatus.in_transit: {ReturnShipmentStatus.received, ReturnShipmentStatus.cancelled},
    ReturnShipmentStatus.received: set(),
    ReturnShipmentStatus.cancelled: set(),
}


class ReturnShipmentService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = ReturnShipmentRepository(session, organization_id, is_superuser)
        self.return_request_repo = ReturnRequestRepository(session, organization_id, is_superuser)
        self.order_repo = OrderRepository(session, organization_id, is_superuser)
        self.warehouse_repo = WarehouseRepository(session, organization_id, is_superuser)
        self.return_service = ReturnService(session, organization_id, is_superuser)

    def _generate_number(self) -> str:
        return f"RS-{uuid4().hex[:10].upper()}"

    async def create_return_shipment(self, data, created_by: str | None = None) -> ReturnShipment:
        return_request = await self.return_request_repo.get_by_id(data.return_request_id)
        if not return_request:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return request not found.")
        if return_request.status not in (ReturnStatus.approved, ReturnStatus.awaiting_pickup):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The return request must be approved before scheduling reverse logistics.")

        existing = await self.repo.get_for_return_request(data.return_request_id)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A return shipment already exists for this return request.")

        warehouse = await self.warehouse_repo.get_by_id(data.warehouse_id)
        if not warehouse:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found.")

        order = await self.order_repo.get_by_id(return_request.order_id)

        number = self._generate_number()
        while await self.repo.get_by_number(number):
            number = self._generate_number()

        return_shipment = ReturnShipment(
            return_shipment_number=number,
            return_request_id=data.return_request_id,
            warehouse_id=data.warehouse_id,
            shipping_provider_id=data.shipping_provider_id,
            pickup_contact_name=f"{order.shipping_first_name} {order.shipping_last_name}" if order else None,
            pickup_contact_phone=order.shipping_phone if order else None,
            pickup_line1=order.shipping_line1 if order else None,
            pickup_city=order.shipping_city if order else None,
            pickup_state=order.shipping_state if order else None,
            pickup_postal_code=order.shipping_postal_code if order else None,
            pickup_country=order.shipping_country if order else None,
            notes=data.notes,
            created_by=created_by,
        )
        return await self.repo.create(return_shipment)

    async def _get_or_404(self, return_shipment_id: str) -> ReturnShipment:
        return_shipment = await self.repo.get_by_id(return_shipment_id)
        if not return_shipment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return shipment not found.")
        return return_shipment

    async def get_return_shipment(self, return_shipment_id: str) -> ReturnShipment | None:
        return await self.repo.get_by_id(return_shipment_id)

    async def list_return_shipments(
        self,
        warehouse_id: str | None = None,
        status_filter: ReturnShipmentStatus | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ReturnShipment], int]:
        items = await self.repo.list(warehouse_id, status_filter, sort_by, sort_order, limit, offset)
        total = await self.repo.count(warehouse_id, status_filter)
        return items, total

    async def _transition(self, return_shipment_id: str, new_status: ReturnShipmentStatus) -> ReturnShipment:
        return_shipment = await self._get_or_404(return_shipment_id)
        allowed = ALLOWED_TRANSITIONS.get(return_shipment.status, set())
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot move a return shipment from '{return_shipment.status.value}' to '{new_status.value}'.",
            )
        return_shipment.status = new_status
        return return_shipment

    async def generate_label(self, return_shipment_id: str) -> ReturnShipment:
        return_shipment = await self._transition(return_shipment_id, ReturnShipmentStatus.label_generated)
        if not return_shipment.tracking_number:
            return_shipment.tracking_number = f"RTRK{uuid4().hex[:12].upper()}"
        return await self.repo.save(return_shipment)

    async def schedule_reverse_pickup(self, return_shipment_id: str, data) -> ReturnShipment:
        return_shipment = await self._transition(return_shipment_id, ReturnShipmentStatus.reverse_pickup_scheduled)
        return_shipment.reverse_pickup_scheduled_at = data.scheduled_at
        return await self.repo.save(return_shipment)

    async def mark_in_transit(self, return_shipment_id: str) -> ReturnShipment:
        return_shipment = await self._transition(return_shipment_id, ReturnShipmentStatus.in_transit)
        return_shipment.reverse_pickup_completed_at = datetime.utcnow()
        return await self.repo.save(return_shipment)

    async def mark_received(self, return_shipment_id: str) -> ReturnShipment:
        return_shipment = await self._transition(return_shipment_id, ReturnShipmentStatus.received)
        return_shipment.received_at = datetime.utcnow()
        return_shipment = await self.repo.save(return_shipment)

        try:
            await self.return_service.mark_received(return_shipment.return_request_id, warehouse_id=return_shipment.warehouse_id)
        except HTTPException:
            pass

        return return_shipment

    async def cancel_return_shipment(self, return_shipment_id: str, reason: str | None = None) -> ReturnShipment:
        return_shipment = await self._transition(return_shipment_id, ReturnShipmentStatus.cancelled)
        return_shipment.cancelled_at = datetime.utcnow()
        if reason:
            return_shipment.notes = f"{return_shipment.notes}\n{reason}" if return_shipment.notes else reason
        return await self.repo.save(return_shipment)
