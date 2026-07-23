from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.models.return_shipment import ReturnShipmentStatus as ModelReturnShipmentStatus
from app.schemas.return_shipment import (
    ReturnShipmentCancelRequest,
    ReturnShipmentCreateRequest,
    ReturnShipmentListResponse,
    ReturnShipmentRead,
    ReturnShipmentSchedulePickupRequest,
)
from app.services.audit_service import AuditService
from app.services.return_shipment_service import ReturnShipmentService

router = APIRouter(prefix="/return-shipments", tags=["shipping-return-shipments"])


def _service(db: AsyncSession, current_user) -> ReturnShipmentService:
    return ReturnShipmentService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=ReturnShipmentListResponse)
async def list_return_shipments(
    warehouse_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("shipping.returns.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _service(db, current_user)
    model_status = ModelReturnShipmentStatus(status_filter) if status_filter else None
    items, total = await service.list_return_shipments(warehouse_id, model_status, sort_by, sort_order, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=ReturnShipmentRead, status_code=status.HTTP_201_CREATED)
async def create_return_shipment(
    data: ReturnShipmentCreateRequest,
    current_user=Depends(require_permission("shipping.returns.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _service(db, current_user)
    return_shipment = await service.create_return_shipment(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="shipping", entity="ReturnShipment", entity_id=return_shipment.id,
        user_id=current_user.id, after={"return_shipment_number": return_shipment.return_shipment_number}, context=audit_context,
    )
    return return_shipment


@router.get("/{return_shipment_id}", response_model=ReturnShipmentRead)
async def get_return_shipment(return_shipment_id: str, current_user=Depends(require_permission("shipping.returns.view")), db: AsyncSession = Depends(get_db)):
    service = _service(db, current_user)
    return_shipment = await service.get_return_shipment(return_shipment_id)
    if not return_shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return shipment not found.")
    return return_shipment


@router.post("/{return_shipment_id}/label", response_model=ReturnShipmentRead)
async def generate_return_label(
    return_shipment_id: str,
    current_user=Depends(require_permission("shipping.returns.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _service(db, current_user)
    return_shipment = await service.generate_label(return_shipment_id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="shipping", entity="ReturnShipment", entity_id=return_shipment.id,
        user_id=current_user.id, after={"status": return_shipment.status.value}, context=audit_context,
    )
    return return_shipment


@router.post("/{return_shipment_id}/schedule-pickup", response_model=ReturnShipmentRead)
async def schedule_reverse_pickup(
    return_shipment_id: str,
    data: ReturnShipmentSchedulePickupRequest,
    current_user=Depends(require_permission("shipping.returns.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _service(db, current_user)
    return_shipment = await service.schedule_reverse_pickup(return_shipment_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="shipping", entity="ReturnShipment", entity_id=return_shipment.id,
        user_id=current_user.id, after={"status": return_shipment.status.value}, context=audit_context,
    )
    return return_shipment


@router.post("/{return_shipment_id}/in-transit", response_model=ReturnShipmentRead)
async def mark_return_shipment_in_transit(
    return_shipment_id: str,
    current_user=Depends(require_permission("shipping.returns.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _service(db, current_user)
    return_shipment = await service.mark_in_transit(return_shipment_id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="shipping", entity="ReturnShipment", entity_id=return_shipment.id,
        user_id=current_user.id, after={"status": return_shipment.status.value}, context=audit_context,
    )
    return return_shipment


@router.post("/{return_shipment_id}/receive", response_model=ReturnShipmentRead)
async def mark_return_shipment_received(
    return_shipment_id: str,
    current_user=Depends(require_permission("shipping.returns.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _service(db, current_user)
    return_shipment = await service.mark_received(return_shipment_id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="shipping", entity="ReturnShipment", entity_id=return_shipment.id,
        user_id=current_user.id, after={"status": return_shipment.status.value}, context=audit_context,
    )
    return return_shipment


@router.post("/{return_shipment_id}/cancel", response_model=ReturnShipmentRead)
async def cancel_return_shipment(
    return_shipment_id: str,
    data: ReturnShipmentCancelRequest,
    current_user=Depends(require_permission("shipping.returns.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _service(db, current_user)
    return_shipment = await service.cancel_return_shipment(return_shipment_id, reason=data.reason)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="shipping", entity="ReturnShipment", entity_id=return_shipment.id,
        user_id=current_user.id, after={"status": "cancelled", "reason": data.reason}, context=audit_context,
    )
    return return_shipment
