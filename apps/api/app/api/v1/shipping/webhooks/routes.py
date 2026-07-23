from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.schemas.shipment_tracking import ShipmentTrackingEventRead, ShipmentTrackingWebhookRequest
from app.services.shipment_tracking_service import ShipmentTrackingService

router = APIRouter(prefix="/webhooks", tags=["shipping-webhooks"])


@router.post("/tracking", response_model=ShipmentTrackingEventRead)
async def receive_tracking_webhook(
    data: ShipmentTrackingWebhookRequest,
    organization_id: str = Query(..., description="Organization this carrier account belongs to."),
    x_webhook_secret: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Inbound tracking webhook for carriers. Not staff-authenticated -- the
    carrier authenticates via the X-Webhook-Secret header, checked against
    the matching ShippingProvider.webhook_secret."""
    service = ShipmentTrackingService(db, organization_id=organization_id)
    return await service.process_webhook(data, webhook_secret=x_webhook_secret)
