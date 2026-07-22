from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.models.stock_adjustment import StockAdjustmentReason as ModelStockAdjustmentReason
from app.schemas.stock_adjustment import (
    StockAdjustmentCreateRequest,
    StockAdjustmentItem,
    StockAdjustmentListResponse,
)
from app.services.audit_service import AuditService
from app.services.stock_adjustment_service import StockAdjustmentService

router = APIRouter(prefix="/adjustments", tags=["inventory-adjustments"])


def _adjustment_service(db: AsyncSession, current_user) -> StockAdjustmentService:
    return StockAdjustmentService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=StockAdjustmentListResponse)
async def list_adjustments(
    warehouse_id: str | None = Query(None),
    product_id: str | None = Query(None),
    reason_filter: str | None = Query(None, alias="reason"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("inventory.adjustments.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _adjustment_service(db, current_user)
    model_reason = ModelStockAdjustmentReason(reason_filter) if reason_filter else None
    items, total = await service.list_adjustments(warehouse_id, product_id, model_reason, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=StockAdjustmentItem, status_code=status.HTTP_201_CREATED)
async def create_adjustment(
    data: StockAdjustmentCreateRequest,
    current_user=Depends(require_permission("inventory.adjustments.create")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _adjustment_service(db, current_user)
    adjustment = await service.create_adjustment(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="inventory", entity="StockAdjustment", entity_id=adjustment.id,
        user_id=current_user.id, after={"quantity_delta": adjustment.quantity_delta, "reason": adjustment.reason.value}, context=audit_context,
    )
    return adjustment


@router.get("/{adjustment_id}", response_model=StockAdjustmentItem)
async def get_adjustment(adjustment_id: str, current_user=Depends(require_permission("inventory.adjustments.view")), db: AsyncSession = Depends(get_db)):
    service = _adjustment_service(db, current_user)
    adjustment = await service.get_adjustment(adjustment_id)
    if not adjustment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock adjustment not found.")
    return adjustment
