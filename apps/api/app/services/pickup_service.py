from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pickup import Pickup, PickupStatus
from app.repositories.pickup_repository import PickupRepository
from app.repositories.shipment_repository import ShipmentRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.services.shipment_service import ShipmentService

ALLOWED_TRANSITIONS: dict[PickupStatus, set[PickupStatus]] = {
    PickupStatus.scheduled: {PickupStatus.confirmed, PickupStatus.cancelled, PickupStatus.missed},
    PickupStatus.confirmed: {PickupStatus.completed, PickupStatus.cancelled, PickupStatus.missed},
    PickupStatus.completed: set(),
    PickupStatus.cancelled: set(),
    PickupStatus.missed: {PickupStatus.scheduled},
}


class PickupService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = PickupRepository(session, organization_id, is_superuser)
        self.shipment_repo = ShipmentRepository(session, organization_id, is_superuser)
        self.warehouse_repo = WarehouseRepository(session, organization_id, is_superuser)
        self.shipment_service = ShipmentService(session, organization_id, is_superuser)

    def _generate_pickup_number(self) -> str:
        return f"PU-{uuid4().hex[:10].upper()}"

    async def schedule_pickup(self, data, created_by: str | None = None) -> Pickup:
        warehouse = await self.warehouse_repo.get_by_id(data.warehouse_id)
        if not warehouse:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found.")

        shipments = []
        for shipment_id in data.shipment_ids:
            shipment = await self.shipment_repo.get_by_id(shipment_id)
            if not shipment:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Shipment {shipment_id} not found.")
            if shipment.warehouse_id != data.warehouse_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Shipment {shipment.shipment_number} does not ship from this warehouse.")
            shipments.append(shipment)

        pickup_number = self._generate_pickup_number()
        while await self.repo.get_by_number(pickup_number):
            pickup_number = self._generate_pickup_number()

        pickup = Pickup(
            pickup_number=pickup_number,
            warehouse_id=data.warehouse_id,
            shipping_provider_id=data.shipping_provider_id,
            scheduled_date=data.scheduled_date,
            time_slot=data.time_slot,
            contact_name=data.contact_name,
            contact_phone=data.contact_phone,
            notes=data.notes,
            created_by=created_by,
        )
        self.repo._add_tenant_on_create(pickup)
        self.session.add(pickup)
        await self.session.flush()

        for shipment in shipments:
            shipment.pickup_id = pickup.id
            await self.shipment_repo.save_no_commit(shipment)

        await self.session.commit()
        await self.session.refresh(pickup)
        return pickup

    async def _get_or_404(self, pickup_id: str) -> Pickup:
        pickup = await self.repo.get_by_id(pickup_id)
        if not pickup:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pickup not found.")
        return pickup

    async def get_pickup(self, pickup_id: str) -> Pickup | None:
        return await self.repo.get_by_id(pickup_id)

    async def list_pickups(
        self,
        warehouse_id: str | None = None,
        status_filter: PickupStatus | None = None,
        sort_by: str = "scheduled_date",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Pickup], int]:
        items = await self.repo.list(warehouse_id, status_filter, sort_by, sort_order, limit, offset)
        total = await self.repo.count(warehouse_id, status_filter)
        return items, total

    async def get_shipments(self, pickup_id: str):
        await self._get_or_404(pickup_id)
        return await self.shipment_repo.list_for_pickup(pickup_id)

    async def _transition(self, pickup_id: str, new_status: PickupStatus) -> Pickup:
        pickup = await self._get_or_404(pickup_id)
        allowed = ALLOWED_TRANSITIONS.get(pickup.status, set())
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot move a pickup from '{pickup.status.value}' to '{new_status.value}'.",
            )
        pickup.status = new_status
        return pickup

    async def confirm_pickup(self, pickup_id: str) -> Pickup:
        pickup = await self._transition(pickup_id, PickupStatus.confirmed)
        return await self.repo.save(pickup)

    async def mark_missed(self, pickup_id: str) -> Pickup:
        pickup = await self._transition(pickup_id, PickupStatus.missed)
        return await self.repo.save(pickup)

    async def reschedule_pickup(self, pickup_id: str, data) -> Pickup:
        pickup = await self._get_or_404(pickup_id)
        if pickup.status not in (PickupStatus.scheduled, PickupStatus.confirmed, PickupStatus.missed):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot reschedule a pickup in '{pickup.status.value}' status.")

        pickup.scheduled_date = data.scheduled_date
        pickup.time_slot = data.time_slot
        pickup.status = PickupStatus.scheduled
        return await self.repo.save(pickup)

    async def complete_pickup(self, pickup_id: str) -> Pickup:
        pickup = await self._transition(pickup_id, PickupStatus.completed)
        pickup.completed_at = datetime.utcnow()
        pickup = await self.repo.save(pickup)

        shipments = await self.get_shipments(pickup_id)
        for shipment in shipments:
            try:
                await self.shipment_service.mark_picked_up(shipment.id)
            except HTTPException:
                pass

        return pickup

    async def cancel_pickup(self, pickup_id: str, reason: str | None = None) -> Pickup:
        pickup = await self._transition(pickup_id, PickupStatus.cancelled)
        pickup.cancelled_at = datetime.utcnow()
        pickup.cancelled_reason = reason
        pickup = await self.repo.save_no_commit(pickup)

        shipments = await self.shipment_repo.list_for_pickup(pickup_id)
        for shipment in shipments:
            shipment.pickup_id = None
            await self.shipment_repo.save_no_commit(shipment)

        await self.session.commit()
        await self.session.refresh(pickup)
        return pickup
