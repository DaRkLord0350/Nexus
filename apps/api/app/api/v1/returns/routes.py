from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.models.return_request import ReturnStatus as ModelReturnStatus
from app.schemas.return_request import (
    ReturnApproveRequest,
    ReturnCancelRequest,
    ReturnCompleteRequest,
    ReturnItemInspectionRequest,
    ReturnItemRead,
    ReturnReceiveRequest,
    ReturnRejectRequest,
    ReturnRequestCreateRequest,
    ReturnRequestDetail,
    ReturnRequestListResponse,
    ReturnRequestRead,
)
from app.services.audit_service import AuditService
from app.services.return_service import ReturnService

router = APIRouter(prefix="/returns", tags=["returns"])


def _return_service(db: AsyncSession, current_user) -> ReturnService:
    return ReturnService(db, current_user.organization_id, current_user.is_superuser)


async def _build_detail(service: ReturnService, return_request) -> ReturnRequestDetail:
    items = await service.get_items(return_request.id)
    detail = ReturnRequestDetail.model_validate(return_request)
    detail.items = [ReturnItemRead.model_validate(item) for item in items]
    return detail


@router.get("/", response_model=ReturnRequestListResponse)
async def list_returns(
    order_id: str | None = Query(None),
    customer_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    q: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("returns.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _return_service(db, current_user)
    model_status = ModelReturnStatus(status_filter) if status_filter else None
    items, total = await service.list_returns(order_id, customer_id, model_status, q, sort_by, sort_order, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=ReturnRequestDetail, status_code=status.HTTP_201_CREATED)
async def create_return_request(
    data: ReturnRequestCreateRequest,
    current_user=Depends(require_permission("returns.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _return_service(db, current_user)
    return_request = await service.create_return_request(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="orders", entity="ReturnRequest", entity_id=return_request.id,
        user_id=current_user.id, after={"return_number": return_request.return_number, "order_id": data.order_id}, context=audit_context,
    )
    return await _build_detail(service, return_request)


@router.get("/{return_id}", response_model=ReturnRequestDetail)
async def get_return(return_id: str, current_user=Depends(require_permission("returns.view")), db: AsyncSession = Depends(get_db)):
    service = _return_service(db, current_user)
    return_request = await service.get_return(return_id)
    if not return_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return request not found.")
    return await _build_detail(service, return_request)


@router.post("/{return_id}/approve", response_model=ReturnRequestRead)
async def approve_return(
    return_id: str,
    data: ReturnApproveRequest,
    current_user=Depends(require_permission("returns.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _return_service(db, current_user)
    return_request = await service.approve_return(return_id, changed_by=current_user.id, resolution=data.resolution)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="orders", entity="ReturnRequest", entity_id=return_request.id,
        user_id=current_user.id, after={"status": "approved"}, context=audit_context,
    )
    return return_request


@router.post("/{return_id}/reject", response_model=ReturnRequestRead)
async def reject_return(
    return_id: str,
    data: ReturnRejectRequest,
    current_user=Depends(require_permission("returns.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _return_service(db, current_user)
    return_request = await service.reject_return(return_id, changed_by=current_user.id, reason=data.reason)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="orders", entity="ReturnRequest", entity_id=return_request.id,
        user_id=current_user.id, after={"status": "rejected", "reason": data.reason}, context=audit_context,
    )
    return return_request


@router.post("/{return_id}/awaiting-pickup", response_model=ReturnRequestRead)
async def mark_return_awaiting_pickup(return_id: str, current_user=Depends(require_permission("returns.manage")), db: AsyncSession = Depends(get_db)):
    service = _return_service(db, current_user)
    return await service.mark_awaiting_pickup(return_id)


@router.post("/{return_id}/in-transit", response_model=ReturnRequestRead)
async def mark_return_in_transit(return_id: str, current_user=Depends(require_permission("returns.manage")), db: AsyncSession = Depends(get_db)):
    service = _return_service(db, current_user)
    return await service.mark_in_transit(return_id)


@router.post("/{return_id}/receive", response_model=ReturnRequestRead)
async def receive_return(
    return_id: str,
    data: ReturnReceiveRequest,
    current_user=Depends(require_permission("returns.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _return_service(db, current_user)
    return_request = await service.mark_received(return_id, warehouse_id=data.warehouse_id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="orders", entity="ReturnRequest", entity_id=return_request.id,
        user_id=current_user.id, after={"status": "received"}, context=audit_context,
    )
    return return_request


@router.post("/{return_id}/inspect", response_model=ReturnRequestRead)
async def start_return_inspection(
    return_id: str,
    current_user=Depends(require_permission("returns.manage")),
    db: AsyncSession = Depends(get_db),
):
    service = _return_service(db, current_user)
    return await service.start_inspection(return_id, changed_by=current_user.id)


@router.patch("/{return_id}/items/{item_id}/inspection", response_model=ReturnItemRead)
async def inspect_return_item(
    return_id: str,
    item_id: str,
    data: ReturnItemInspectionRequest,
    current_user=Depends(require_permission("returns.manage")),
    db: AsyncSession = Depends(get_db),
):
    service = _return_service(db, current_user)
    return await service.update_item_inspection(return_id, item_id, condition=data.condition, reason_code=data.reason_code)


@router.post("/{return_id}/complete", response_model=ReturnRequestRead)
async def complete_return(
    return_id: str,
    data: ReturnCompleteRequest,
    current_user=Depends(require_permission("returns.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _return_service(db, current_user)
    return_request = await service.complete_return(return_id, resolution=data.resolution, restock=data.restock, changed_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="orders", entity="ReturnRequest", entity_id=return_request.id,
        user_id=current_user.id, after={"status": "completed", "resolution": data.resolution.value}, context=audit_context,
    )
    return return_request


@router.post("/{return_id}/cancel", response_model=ReturnRequestRead)
async def cancel_return(
    return_id: str,
    data: ReturnCancelRequest,
    current_user=Depends(require_permission("returns.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _return_service(db, current_user)
    return_request = await service.cancel_return(return_id, reason=data.reason)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="orders", entity="ReturnRequest", entity_id=return_request.id,
        user_id=current_user.id, after={"status": "cancelled"}, context=audit_context,
    )
    return return_request
