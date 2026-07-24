from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_permission
from app.repositories.marketplace_order_link_repository import MarketplaceOrderLinkRepository
from app.schemas.marketplace_order_link import MarketplaceOrderLinkListResponse

router = APIRouter(prefix="/orders", tags=["marketplace-order-links"])


@router.get("/links", response_model=MarketplaceOrderLinkListResponse)
async def list_marketplace_order_links(
    connector_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("marketplace.orders.view")),
    db: AsyncSession = Depends(get_db),
):
    repo = MarketplaceOrderLinkRepository(db, current_user.organization_id, current_user.is_superuser)
    items = await repo.list(connector_id, status_filter, limit, offset)
    total = await repo.count(connector_id, status_filter)
    return {"items": items, "total": total, "limit": limit, "offset": offset}
