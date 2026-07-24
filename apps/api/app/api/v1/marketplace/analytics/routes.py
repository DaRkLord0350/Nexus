from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_permission
from app.schemas.marketplace_analytics import MarketplaceAnalyticsResponse
from app.services.marketplace_analytics_service import MarketplaceAnalyticsService

router = APIRouter(prefix="/analytics", tags=["marketplace-analytics"])


@router.get("/dashboard", response_model=MarketplaceAnalyticsResponse)
async def get_marketplace_analytics_dashboard(
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    current_user=Depends(require_permission("marketplace.analytics.view")),
    db: AsyncSession = Depends(get_db),
):
    service = MarketplaceAnalyticsService(db, current_user.organization_id, current_user.is_superuser)
    return await service.get_dashboard(date_from, date_to)
