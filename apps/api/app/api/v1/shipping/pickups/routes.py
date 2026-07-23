from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.models.pickup import PickupStatus as ModelPickupStatus
from app.schemas.pickup import (
    PickupCancelRequest,
    PickupCreateRequest,
    PickupListResponse,
    PickupRead,
    PickupRescheduleRequest,
)
from app.services.audit_service import AuditService
from app.services.pickup_service import PickupService

router = APIRouter(prefix="/pickups", tags=["shipping-pickups"])


def _pickup_service(db: AsyncSession, current_user) -> PickupService:
    return PickupService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=PickupListResponse)
async def list_pickups(
    warehouse_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    sort_by: str = Query("scheduled_date"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("shipping.pickups.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _pickup_service(db, current_user)
    model_status = ModelPickupStatus(status_filter) if status_filter else None
    items, total = await service.list_pickups(warehouse_id, model_status, sort_by, sort_order, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=PickupRead, status_code=status.HTTP_201_CREATED)
async def schedule_pickup(
    data: PickupCreateRequest,
    current_user=Depends(require_permission("shipping.pickups.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _pickup_service(db, current_user)
    pickup = await service.schedule_pickup(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="shipping", entity="Pickup", entity_id=pickup.id,
        user_id=current_user.id, after={"pickup_number": pickup.pickup_number, "warehouse_id": data.warehouse_id}, context=audit_context,
    )
    return pickup


@router.get("/{pickup_id}", response_model=PickupRead)
async def get_pickup(pickup_id: str, current_user=Depends(require_permission("shipping.pickups.view")), db: AsyncSession = Depends(get_db)):
    service = _pickup_service(db, current_user)
    pickup = await service.get_pickup(pickup_id)
    if not pickup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pickup not found.")
    return pickup


@router.post("/{pickup_id}/confirm", response_model=PickupRead)
async def confirm_pickup(
    pickup_id: str,
    current_user=Depends(require_permission("shipping.pickups.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _pickup_service(db, current_user)
    pickup = await service.confirm_pickup(pickup_id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="shipping", entity="Pickup", entity_id=pickup.id,
        user_id=current_user.id, after={"status": "confirmed"}, context=audit_context,
    )
    return pickup


@router.post("/{pickup_id}/reschedule", response_model=PickupRead)
async def reschedule_pickup(
    pickup_id: str,
    data: PickupRescheduleRequest,
    current_user=Depends(require_permission("shipping.pickups.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _pickup_service(db, current_user)
    pickup = await service.reschedule_pickup(pickup_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="shipping", entity="Pickup", entity_id=pickup.id,
        user_id=current_user.id, after={"scheduled_date": data.scheduled_date.isoformat()}, context=audit_context,
    )
    return pickup


@router.post("/{pickup_id}/complete", response_model=PickupRead)
async def complete_pickup(
    pickup_id: str,
    current_user=Depends(require_permission("shipping.pickups.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _pickup_service(db, current_user)
    pickup = await service.complete_pickup(pickup_id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="shipping", entity="Pickup", entity_id=pickup.id,
        user_id=current_user.id, after={"status": "completed"}, context=audit_context,
    )
    return pickup


@router.post("/{pickup_id}/missed", response_model=PickupRead)
async def mark_pickup_missed(
    pickup_id: str,
    current_user=Depends(require_permission("shipping.pickups.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _pickup_service(db, current_user)
    pickup = await service.mark_missed(pickup_id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="shipping", entity="Pickup", entity_id=pickup.id,
        user_id=current_user.id, after={"status": "missed"}, context=audit_context,
    )
    return pickup


@router.post("/{pickup_id}/cancel", response_model=PickupRead)
async def cancel_pickup(
    pickup_id: str,
    data: PickupCancelRequest,
    current_user=Depends(require_permission("shipping.pickups.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _pickup_service(db, current_user)
    pickup = await service.cancel_pickup(pickup_id, reason=data.reason)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="shipping", entity="Pickup", entity_id=pickup.id,
        user_id=current_user.id, after={"status": "cancelled", "reason": data.reason}, context=audit_context,
    )
    return pickup
