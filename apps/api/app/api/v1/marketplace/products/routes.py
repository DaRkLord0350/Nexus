from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_permission
from app.repositories.marketplace_product_link_repository import MarketplaceProductLinkRepository
from app.schemas.marketplace_product_link import MarketplaceProductLinkListResponse

router = APIRouter(prefix="/products", tags=["marketplace-product-links"])


@router.get("/links", response_model=MarketplaceProductLinkListResponse)
async def list_marketplace_product_links(
    connector_id: str | None = Query(None),
    sync_status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("marketplace.listings.view")),
    db: AsyncSession = Depends(get_db),
):
    repo = MarketplaceProductLinkRepository(db, current_user.organization_id, current_user.is_superuser)
    items = await repo.list(connector_id, sync_status, limit, offset)
    total = await repo.count(connector_id, sync_status)
    return {"items": items, "total": total, "limit": limit, "offset": offset}
