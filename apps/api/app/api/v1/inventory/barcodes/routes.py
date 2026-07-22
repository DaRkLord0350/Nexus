from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.models.barcode import BarcodeFormat as ModelBarcodeFormat
from app.schemas.barcode import (
    BarcodeCreateRequest,
    BarcodeItem,
    BarcodeListResponse,
    BarcodeUpdateRequest,
    BulkDeleteRequest,
    QRCodeCreateRequest,
    QRCodeItem,
    QRCodeListResponse,
    QRCodeUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.barcode_service import BarcodeService

router = APIRouter(prefix="/barcodes", tags=["inventory-barcodes"])


def _barcode_service(db: AsyncSession, current_user) -> BarcodeService:
    return BarcodeService(db, current_user.organization_id, current_user.is_superuser)


# --- Barcodes (EAN13 / UPC / Code128 / QR value codes) ---

@router.get("/codes", response_model=BarcodeListResponse)
async def list_barcodes(
    product_id: str | None = Query(None),
    variant_id: str | None = Query(None),
    format_filter: str | None = Query(None, alias="format"),
    q: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("inventory.barcodes.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _barcode_service(db, current_user)
    model_format = ModelBarcodeFormat(format_filter) if format_filter else None
    items, total = await service.list_barcodes(product_id, variant_id, model_format, q, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/codes/lookup", response_model=BarcodeItem)
async def lookup_barcode(
    value: str = Query(..., min_length=1),
    format_filter: str | None = Query(None, alias="format"),
    current_user=Depends(require_permission("inventory.barcodes.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _barcode_service(db, current_user)
    model_format = ModelBarcodeFormat(format_filter) if format_filter else None
    barcode = await service.lookup(value, model_format)
    if not barcode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching barcode found.")
    return barcode


@router.post("/codes", response_model=BarcodeItem, status_code=status.HTTP_201_CREATED)
async def create_barcode(
    data: BarcodeCreateRequest,
    current_user=Depends(require_permission("inventory.barcodes.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _barcode_service(db, current_user)
    barcode = await service.create_barcode(data)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="inventory", entity="Barcode", entity_id=barcode.id,
        user_id=current_user.id, after={"value": barcode.value, "format": barcode.format.value}, context=audit_context,
    )
    return barcode


@router.post("/codes/bulk-delete")
async def bulk_delete_barcodes(
    data: BulkDeleteRequest,
    current_user=Depends(require_permission("inventory.barcodes.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _barcode_service(db, current_user)
    deleted_count = await service.bulk_delete(data.ids)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="inventory", entity="Barcode", user_id=current_user.id,
        before={"ids": data.ids}, after={"deleted_count": deleted_count}, context=audit_context,
    )
    return {"deleted_count": deleted_count}


@router.get("/codes/{barcode_id}", response_model=BarcodeItem)
async def get_barcode(barcode_id: str, current_user=Depends(require_permission("inventory.barcodes.view")), db: AsyncSession = Depends(get_db)):
    service = _barcode_service(db, current_user)
    barcode = await service.get_barcode(barcode_id)
    if not barcode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Barcode not found.")
    return barcode


@router.patch("/codes/{barcode_id}", response_model=BarcodeItem)
async def update_barcode(
    barcode_id: str,
    data: BarcodeUpdateRequest,
    current_user=Depends(require_permission("inventory.barcodes.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _barcode_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    barcode = await service.update_barcode(barcode_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="Barcode", entity_id=barcode.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return barcode


@router.delete("/codes/{barcode_id}")
async def delete_barcode(
    barcode_id: str,
    current_user=Depends(require_permission("inventory.barcodes.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _barcode_service(db, current_user)
    await service.delete_barcode(barcode_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="inventory", entity="Barcode", entity_id=barcode_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Barcode deleted successfully."}


# --- QR codes (polymorphic: warehouse, bin, batch, serial, product, variant, inventory) ---

@router.get("/qr", response_model=QRCodeListResponse)
async def list_qr_codes(
    entity_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("inventory.barcodes.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _barcode_service(db, current_user)
    items, total = await service.list_qr_codes(entity_type, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/qr/lookup", response_model=QRCodeItem)
async def lookup_qr_code(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    current_user=Depends(require_permission("inventory.barcodes.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _barcode_service(db, current_user)
    qr_code = await service.get_qr_code_for_entity(entity_type, entity_id)
    if not qr_code:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No QR code found for this entity.")
    return qr_code


@router.post("/qr", response_model=QRCodeItem, status_code=status.HTTP_201_CREATED)
async def create_qr_code(
    data: QRCodeCreateRequest,
    current_user=Depends(require_permission("inventory.barcodes.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _barcode_service(db, current_user)
    qr_code = await service.create_qr_code(data)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="inventory", entity="QRCode", entity_id=qr_code.id,
        user_id=current_user.id, after={"entity_type": qr_code.entity_type, "entity_id": qr_code.entity_id}, context=audit_context,
    )
    return qr_code


@router.get("/qr/{qr_code_id}", response_model=QRCodeItem)
async def get_qr_code(qr_code_id: str, current_user=Depends(require_permission("inventory.barcodes.view")), db: AsyncSession = Depends(get_db)):
    service = _barcode_service(db, current_user)
    qr_code = await service.get_qr_code(qr_code_id)
    if not qr_code:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR code not found.")
    return qr_code


@router.patch("/qr/{qr_code_id}", response_model=QRCodeItem)
async def update_qr_code(
    qr_code_id: str,
    data: QRCodeUpdateRequest,
    current_user=Depends(require_permission("inventory.barcodes.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _barcode_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    qr_code = await service.update_qr_code(qr_code_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="QRCode", entity_id=qr_code.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return qr_code


@router.delete("/qr/{qr_code_id}")
async def delete_qr_code(
    qr_code_id: str,
    current_user=Depends(require_permission("inventory.barcodes.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _barcode_service(db, current_user)
    await service.delete_qr_code(qr_code_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="inventory", entity="QRCode", entity_id=qr_code_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "QR code deleted successfully."}
