from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/", response_model=DashboardResponse)
async def get_dashboard(current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    dashboard_service = DashboardService(db, current_user.organization_id, current_user.is_superuser)
    return await dashboard_service.get_dashboard()
