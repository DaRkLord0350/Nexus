from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import require_permission
from app.schemas.marketplace_webhook_event import MarketplaceWebhookEventListResponse, MarketplaceWebhookEventRead, MarketplaceWebhookRequest
from app.services.marketplace_webhook_service import MarketplaceWebhookService

router = APIRouter(prefix="/webhooks", tags=["marketplace-webhooks"])


@router.post("/", response_model=MarketplaceWebhookEventRead)
async def receive_marketplace_webhook(
    data: MarketplaceWebhookRequest,
    organization_id: str = Query(..., description="Organization this marketplace connector belongs to."),
    x_webhook_secret: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Inbound marketplace webhook (order.created, order.updated,
    inventory.updated, ...). Not staff-authenticated -- the marketplace
    authenticates via the X-Webhook-Secret header, checked against the
    matching MarketplaceConnector.webhook_secret."""
    service = MarketplaceWebhookService(db, organization_id=organization_id)
    return await service.process_webhook(data, webhook_secret=x_webhook_secret)


@router.post("/retry", response_model=list[MarketplaceWebhookEventRead])
async def retry_marketplace_webhook_events(
    connector_id: str | None = Query(None),
    current_user=Depends(require_permission("marketplace.sync.manage")),
    db: AsyncSession = Depends(get_db),
):
    """Manually process whatever failed webhook events are currently due
    for retry. Stands in for a scheduled retry worker -- see
    MarketplaceWebhookEvent's module docstring for why."""
    service = MarketplaceWebhookService(db, current_user.organization_id, current_user.is_superuser)
    return await service.retry_due_events(connector_id)


@router.get("/events", response_model=MarketplaceWebhookEventListResponse)
async def list_marketplace_webhook_events(
    connector_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("marketplace.sync.view")),
    db: AsyncSession = Depends(get_db),
):
    service = MarketplaceWebhookService(db, current_user.organization_id, current_user.is_superuser)
    items, total = await service.list_events(connector_id, status_filter, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}
