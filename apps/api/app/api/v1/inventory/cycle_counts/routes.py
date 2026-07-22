from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.models.cycle_count import CycleCountStatus as ModelCycleCountStatus
from app.schemas.cycle_count import (
    CycleCountCreateRequest,
    CycleCountDetail,
    CycleCountLineItem,
    CycleCountListResponse,
    CycleCountRead,
    CycleCountRecordRequest,
)
from app.services.audit_service import AuditService
from app.services.cycle_count_service import CycleCountService

router = APIRouter(prefix="/cycle-counts", tags=["inventory-cycle-counts"])


def _cycle_count_service(db: AsyncSession, current_user) -> CycleCountService:
    return CycleCountService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=CycleCountListResponse)
async def list_cycle_counts(
    warehouse_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    q: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("inventory.cycle_counts.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _cycle_count_service(db, current_user)
    model_status = ModelCycleCountStatus(status_filter) if status_filter else None
    items, total = await service.list_cycle_counts(warehouse_id, model_status, q, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=CycleCountRead, status_code=status.HTTP_201_CREATED)
async def create_cycle_count(
    data: CycleCountCreateRequest,
    current_user=Depends(require_permission("inventory.cycle_counts.create")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _cycle_count_service(db, current_user)
    cycle_count = await service.create_cycle_count(data)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="inventory", entity="CycleCount", entity_id=cycle_count.id,
        user_id=current_user.id, after={"count_number": cycle_count.count_number}, context=audit_context,
    )
    return cycle_count


@router.get("/{cycle_count_id}", response_model=CycleCountDetail)
async def get_cycle_count(cycle_count_id: str, current_user=Depends(require_permission("inventory.cycle_counts.view")), db: AsyncSession = Depends(get_db)):
    service = _cycle_count_service(db, current_user)
    cycle_count = await service.get_cycle_count(cycle_count_id)
    if not cycle_count:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cycle count not found.")
    items = await service.get_items(cycle_count_id)
    detail = CycleCountDetail.model_validate(cycle_count)
    detail.items = [CycleCountLineItem.model_validate(item) for item in items]
    return detail


@router.patch("/{cycle_count_id}/items/{item_id}", response_model=CycleCountLineItem)
async def record_cycle_count_item(
    cycle_count_id: str,
    item_id: str,
    data: CycleCountRecordRequest,
    current_user=Depends(require_permission("inventory.cycle_counts.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _cycle_count_service(db, current_user)
    item = await service.record_count(cycle_count_id, item_id, data, counted_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="CycleCount", entity_id=cycle_count_id,
        user_id=current_user.id, after={"item_id": item.id, "actual_quantity": item.actual_quantity}, context=audit_context,
    )
    return item


@router.post("/{cycle_count_id}/complete", response_model=CycleCountRead)
async def complete_cycle_count(
    cycle_count_id: str,
    current_user=Depends(require_permission("inventory.cycle_counts.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _cycle_count_service(db, current_user)
    cycle_count = await service.complete_count(cycle_count_id, user_id=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="CycleCount", entity_id=cycle_count.id,
        user_id=current_user.id, after={"status": "completed"}, context=audit_context,
    )
    return cycle_count


@router.post("/{cycle_count_id}/cancel", response_model=CycleCountRead)
async def cancel_cycle_count(
    cycle_count_id: str,
    current_user=Depends(require_permission("inventory.cycle_counts.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _cycle_count_service(db, current_user)
    cycle_count = await service.cancel_cycle_count(cycle_count_id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="CycleCount", entity_id=cycle_count.id,
        user_id=current_user.id, after={"status": "cancelled"}, context=audit_context,
    )
    return cycle_count


@router.get("/{cycle_count_id}/items", response_model=list[CycleCountLineItem])
async def list_cycle_count_items(cycle_count_id: str, current_user=Depends(require_permission("inventory.cycle_counts.view")), db: AsyncSession = Depends(get_db)):
    service = _cycle_count_service(db, current_user)
    return await service.get_items(cycle_count_id)
