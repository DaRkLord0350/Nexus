from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_permission
from app.schemas.shipping_analytics import CourierPerformanceResponse
from app.services.shipping_analytics_service import ShippingAnalyticsService

router = APIRouter(prefix="/analytics", tags=["shipping-analytics"])


@router.get("/courier-performance", response_model=CourierPerformanceResponse)
async def get_courier_performance(
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    current_user=Depends(require_permission("shipping.analytics.view")),
    db: AsyncSession = Depends(get_db),
):
    service = ShippingAnalyticsService(db, current_user.organization_id, current_user.is_superuser)
    return await service.get_courier_performance(date_from, date_to)
