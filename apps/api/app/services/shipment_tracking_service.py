import json
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipment import ShipmentStatus
from app.models.shipment_tracking import ShipmentTracking
from app.repositories.shipment_repository import ShipmentRepository
from app.repositories.shipment_tracking_repository import ShipmentTrackingRepository
from app.repositories.shipping_provider_repository import ShippingProviderRepository
from app.services.shipment_service import ShipmentService

# Best-effort mapping from free-text carrier status words to our internal
# ShipmentStatus workflow. Real carriers each use their own vocabulary; a
# production integration would normalize per-carrier before this point.
STATUS_KEYWORD_TO_TRANSITION = {
    "picked_up": "mark_picked_up",
    "pickup": "mark_picked_up",
    "in_transit": "mark_in_transit",
    "shipped": "mark_in_transit",
    "out_for_delivery": "mark_out_for_delivery",
    "delivered": "mark_delivered",
    "failed": "mark_failed_delivery",
    "failed_delivery": "mark_failed_delivery",
    "ndr": "mark_failed_delivery",
    "returned": "mark_returned",
    "returned_to_origin": "mark_returned",
}


class ShipmentTrackingService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = ShipmentTrackingRepository(session, organization_id, is_superuser)
        self.shipment_repo = ShipmentRepository(session, organization_id, is_superuser)
        self.provider_repo = ShippingProviderRepository(session, organization_id, is_superuser)
        self.shipment_service = ShipmentService(session, organization_id, is_superuser)

    async def _sync_shipment_status(self, shipment_id: str, status_text: str) -> None:
        method_name = STATUS_KEYWORD_TO_TRANSITION.get(status_text.strip().lower())
        if not method_name:
            return
        try:
            await getattr(self.shipment_service, method_name)(shipment_id)
        except HTTPException:
            # Best-effort: an out-of-order or duplicate carrier update
            # shouldn't fail the whole tracking-event ingestion.
            pass

    async def add_event(self, shipment_id: str, data, source: str = "manual") -> ShipmentTracking:
        shipment = await self.shipment_repo.get_by_id(shipment_id)
        if not shipment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found.")

        event = ShipmentTracking(
            shipment_id=shipment_id,
            status=data.status,
            description=data.description,
            location=data.location,
            occurred_at=data.occurred_at or datetime.utcnow(),
            source=source,
        )
        event = await self.repo.create(event)
        await self._sync_shipment_status(shipment_id, data.status)
        return event

    async def get_timeline(self, shipment_id: str) -> list[ShipmentTracking]:
        return await self.repo.list_for_shipment(shipment_id)

    async def process_webhook(self, data, webhook_secret: str | None = None) -> ShipmentTracking:
        provider = await self.provider_repo.get_by_code(data.provider_code)
        if not provider:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown shipping provider code.")
        if provider.webhook_secret and provider.webhook_secret != webhook_secret:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret.")

        shipment = await self.shipment_repo.get_by_tracking_number(data.tracking_number)
        if not shipment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No shipment found for that tracking number.")

        event = ShipmentTracking(
            shipment_id=shipment.id,
            status=data.status,
            description=data.description,
            location=data.location,
            occurred_at=data.occurred_at or datetime.utcnow(),
            source="webhook",
            raw_payload=json.dumps(data.model_dump(mode="json")),
        )
        event = await self.repo.create(event)
        await self._sync_shipment_status(shipment.id, data.status)
        return event
