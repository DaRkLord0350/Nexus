from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.models.refund import RefundStatus as ModelRefundStatus
from app.schemas.refund import (
    RefundCreateRequest,
    RefundDetail,
    RefundItemRead,
    RefundListResponse,
    RefundRead,
    RefundRejectRequest,
)
from app.services.audit_service import AuditService
from app.services.refund_service import RefundService

router = APIRouter(prefix="/refunds", tags=["refunds"])


def _refund_service(db: AsyncSession, current_user) -> RefundService:
    return RefundService(db, current_user.organization_id, current_user.is_superuser)


async def _build_detail(service: RefundService, refund) -> RefundDetail:
    items = await service.get_items(refund.id)
    detail = RefundDetail.model_validate(refund)
    detail.items = [RefundItemRead.model_validate(item) for item in items]
    return detail


@router.get("/", response_model=RefundListResponse)
async def list_refunds(
    order_id: str | None = Query(None),
    customer_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    q: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("refunds.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _refund_service(db, current_user)
    model_status = ModelRefundStatus(status_filter) if status_filter else None
    items, total = await service.list_refunds(order_id, customer_id, model_status, q, sort_by, sort_order, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=RefundDetail, status_code=status.HTTP_201_CREATED)
async def create_refund(
    data: RefundCreateRequest,
    current_user=Depends(require_permission("refunds.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _refund_service(db, current_user)
    refund = await service.create_refund_request(data, requested_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="orders", entity="Refund", entity_id=refund.id,
        user_id=current_user.id, after={"refund_number": refund.refund_number, "amount": refund.amount}, context=audit_context,
    )
    return await _build_detail(service, refund)


@router.get("/{refund_id}", response_model=RefundDetail)
async def get_refund(refund_id: str, current_user=Depends(require_permission("refunds.view")), db: AsyncSession = Depends(get_db)):
    service = _refund_service(db, current_user)
    refund = await service.get_refund(refund_id)
    if not refund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refund not found.")
    return await _build_detail(service, refund)


@router.post("/{refund_id}/approve", response_model=RefundRead)
async def approve_refund(
    refund_id: str,
    current_user=Depends(require_permission("refunds.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _refund_service(db, current_user)
    refund = await service.approve_refund(refund_id, changed_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="orders", entity="Refund", entity_id=refund.id,
        user_id=current_user.id, after={"status": "approved"}, context=audit_context,
    )
    return refund


@router.post("/{refund_id}/reject", response_model=RefundRead)
async def reject_refund(
    refund_id: str,
    data: RefundRejectRequest,
    current_user=Depends(require_permission("refunds.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _refund_service(db, current_user)
    refund = await service.reject_refund(refund_id, changed_by=current_user.id, reason=data.reason)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="orders", entity="Refund", entity_id=refund.id,
        user_id=current_user.id, after={"status": "rejected", "reason": data.reason}, context=audit_context,
    )
    return refund


@router.post("/{refund_id}/complete", response_model=RefundRead)
async def complete_refund(
    refund_id: str,
    current_user=Depends(require_permission("refunds.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _refund_service(db, current_user)
    refund = await service.complete_refund(refund_id, changed_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="orders", entity="Refund", entity_id=refund.id,
        user_id=current_user.id, after={"status": "completed", "amount": refund.amount}, context=audit_context,
    )
    return refund


@router.post("/{refund_id}/fail", response_model=RefundRead)
async def fail_refund(
    refund_id: str,
    data: RefundRejectRequest,
    current_user=Depends(require_permission("refunds.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _refund_service(db, current_user)
    refund = await service.fail_refund(refund_id, changed_by=current_user.id, reason=data.reason)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="orders", entity="Refund", entity_id=refund.id,
        user_id=current_user.id, after={"status": "failed", "reason": data.reason}, context=audit_context,
    )
    return refund
