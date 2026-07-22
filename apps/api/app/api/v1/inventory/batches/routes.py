from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.models.batch import BatchStatus as ModelBatchStatus
from app.schemas.batch import (
    BatchCreateRequest,
    BatchItem,
    BatchListResponse,
    BatchUpdateRequest,
    BulkDeleteRequest,
)
from app.services.audit_service import AuditService
from app.services.batch_service import BatchService

router = APIRouter(prefix="/batches", tags=["inventory-batches"])


def _batch_service(db: AsyncSession, current_user) -> BatchService:
    return BatchService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=BatchListResponse)
async def list_batches(
    product_id: str | None = Query(None),
    warehouse_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    expiring_before: datetime | None = Query(None),
    q: str | None = Query(None),
    sort_by: str = Query("expiry_date"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("inventory.batches.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _batch_service(db, current_user)
    model_status = ModelBatchStatus(status_filter) if status_filter else None
    items, total = await service.list_batches(product_id, warehouse_id, model_status, expiring_before, q, sort_by, sort_order, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=BatchItem, status_code=status.HTTP_201_CREATED)
async def create_batch(
    data: BatchCreateRequest,
    current_user=Depends(require_permission("inventory.batches.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _batch_service(db, current_user)
    batch = await service.create_batch(data)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="inventory", entity="Batch", entity_id=batch.id,
        user_id=current_user.id, after={"batch_number": batch.batch_number}, context=audit_context,
    )
    return batch


@router.post("/bulk-delete")
async def bulk_delete_batches(
    data: BulkDeleteRequest,
    current_user=Depends(require_permission("inventory.batches.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _batch_service(db, current_user)
    deleted_count = 0
    for batch_id in data.ids:
        try:
            await service.delete_batch(batch_id)
            deleted_count += 1
        except HTTPException:
            continue
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="inventory", entity="Batch", user_id=current_user.id,
        before={"ids": data.ids}, after={"deleted_count": deleted_count}, context=audit_context,
    )
    return {"deleted_count": deleted_count}


@router.get("/{batch_id}", response_model=BatchItem)
async def get_batch(batch_id: str, current_user=Depends(require_permission("inventory.batches.view")), db: AsyncSession = Depends(get_db)):
    service = _batch_service(db, current_user)
    batch = await service.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found.")
    return batch


@router.patch("/{batch_id}", response_model=BatchItem)
async def update_batch(
    batch_id: str,
    data: BatchUpdateRequest,
    current_user=Depends(require_permission("inventory.batches.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _batch_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    batch = await service.update_batch(batch_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="Batch", entity_id=batch.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return batch


@router.delete("/{batch_id}")
async def delete_batch(
    batch_id: str,
    current_user=Depends(require_permission("inventory.batches.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _batch_service(db, current_user)
    await service.delete_batch(batch_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="inventory", entity="Batch", entity_id=batch_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Batch deleted successfully."}
