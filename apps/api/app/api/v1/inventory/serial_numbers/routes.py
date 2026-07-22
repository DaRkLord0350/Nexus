from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.models.serial_number import SerialStatus as ModelSerialStatus
from app.schemas.serial_number import (
    BulkDeleteRequest,
    SerialNumberBulkImportRequest,
    SerialNumberCreateRequest,
    SerialNumberItem,
    SerialNumberListResponse,
    SerialNumberUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.serial_number_service import SerialNumberService

router = APIRouter(prefix="/serial-numbers", tags=["inventory-serial-numbers"])


def _serial_service(db: AsyncSession, current_user) -> SerialNumberService:
    return SerialNumberService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=SerialNumberListResponse)
async def list_serial_numbers(
    product_id: str | None = Query(None),
    warehouse_id: str | None = Query(None),
    batch_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    q: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("inventory.serials.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _serial_service(db, current_user)
    model_status = ModelSerialStatus(status_filter) if status_filter else None
    items, total = await service.list_serials(product_id, warehouse_id, batch_id, model_status, q, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/scan", response_model=SerialNumberItem)
async def scan_serial_number(
    serial: str = Query(..., min_length=1),
    current_user=Depends(require_permission("inventory.serials.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _serial_service(db, current_user)
    serial_number = await service.scan(serial)
    if not serial_number:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching serial number found.")
    return serial_number


@router.post("/", response_model=SerialNumberItem, status_code=status.HTTP_201_CREATED)
async def create_serial_number(
    data: SerialNumberCreateRequest,
    current_user=Depends(require_permission("inventory.serials.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _serial_service(db, current_user)
    serial_number = await service.create_serial(data)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="inventory", entity="SerialNumber", entity_id=serial_number.id,
        user_id=current_user.id, after={"serial": serial_number.serial}, context=audit_context,
    )
    return serial_number


@router.post("/import")
async def import_serial_numbers(
    data: SerialNumberBulkImportRequest,
    current_user=Depends(require_permission("inventory.serials.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _serial_service(db, current_user)
    created, skipped = await service.bulk_import(data)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="inventory", entity="SerialNumber", user_id=current_user.id,
        after={"imported_count": len(created), "skipped_count": len(skipped)}, context=audit_context,
    )
    return {"imported_count": len(created), "skipped": skipped}


@router.post("/bulk-delete")
async def bulk_delete_serial_numbers(
    data: BulkDeleteRequest,
    current_user=Depends(require_permission("inventory.serials.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _serial_service(db, current_user)
    deleted_count = await service.bulk_delete(data.ids)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="inventory", entity="SerialNumber", user_id=current_user.id,
        before={"ids": data.ids}, after={"deleted_count": deleted_count}, context=audit_context,
    )
    return {"deleted_count": deleted_count}


@router.get("/{serial_id}", response_model=SerialNumberItem)
async def get_serial_number(serial_id: str, current_user=Depends(require_permission("inventory.serials.view")), db: AsyncSession = Depends(get_db)):
    service = _serial_service(db, current_user)
    serial_number = await service.get_serial(serial_id)
    if not serial_number:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Serial number not found.")
    return serial_number


@router.patch("/{serial_id}", response_model=SerialNumberItem)
async def update_serial_number(
    serial_id: str,
    data: SerialNumberUpdateRequest,
    current_user=Depends(require_permission("inventory.serials.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _serial_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    serial_number = await service.update_serial(serial_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="SerialNumber", entity_id=serial_number.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return serial_number


@router.delete("/{serial_id}")
async def delete_serial_number(
    serial_id: str,
    current_user=Depends(require_permission("inventory.serials.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _serial_service(db, current_user)
    await service.delete_serial(serial_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="inventory", entity="SerialNumber", entity_id=serial_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Serial number deleted successfully."}
