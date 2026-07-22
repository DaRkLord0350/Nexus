from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_current_active_user, get_db, require_permission
from app.models.variant import VariantStatus as ModelVariantStatus
from app.schemas.variant import (
    BulkDeleteRequest,
    VariantCreateRequest,
    VariantItem,
    VariantListResponse,
    VariantStatus,
    VariantUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.variant_service import VariantService

router = APIRouter(prefix="/products/{product_id}/variants", tags=["catalog-variants"])


def _variant_service(db: AsyncSession, current_user) -> VariantService:
    return VariantService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=VariantListResponse)
async def list_variants(
    product_id: str,
    status_filter: VariantStatus | None = Query(None, alias="status"),
    q: str | None = Query(None),
    sort_by: str = Query("sort_order"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("catalog.products.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _variant_service(db, current_user)
    model_status = ModelVariantStatus(status_filter.value) if status_filter else None
    items, total = await service.list_variants(product_id, model_status, q, sort_by, sort_order, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=VariantItem, status_code=status.HTTP_201_CREATED)
async def create_variant(
    product_id: str,
    data: VariantCreateRequest,
    current_user=Depends(require_permission("catalog.variants.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _variant_service(db, current_user)
    variant = await service.create_variant(product_id, data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="catalog", entity="Variant", entity_id=variant.id,
        user_id=current_user.id, after={"sku": variant.sku, "product_id": product_id}, context=audit_context,
    )
    return variant


@router.post("/bulk-delete")
async def bulk_delete_variants(
    product_id: str,
    data: BulkDeleteRequest,
    current_user=Depends(require_permission("catalog.variants.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _variant_service(db, current_user)
    deleted_count = await service.bulk_delete(data.ids)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="Variant", user_id=current_user.id,
        before={"ids": data.ids}, after={"deleted_count": deleted_count}, context=audit_context,
    )
    return {"deleted_count": deleted_count}


@router.get("/{variant_id}", response_model=VariantItem)
async def get_variant(
    product_id: str,
    variant_id: str,
    current_user=Depends(require_permission("catalog.products.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _variant_service(db, current_user)
    variant = await service.get_variant(variant_id)
    if not variant or variant.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found.")
    return variant


@router.patch("/{variant_id}", response_model=VariantItem)
async def update_variant(
    product_id: str,
    variant_id: str,
    data: VariantUpdateRequest,
    current_user=Depends(require_permission("catalog.variants.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _variant_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    variant = await service.update_variant(variant_id, data)
    if variant.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found.")
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="Variant", entity_id=variant.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return variant


@router.post("/{variant_id}/set-default", response_model=VariantItem)
async def set_default_variant(
    product_id: str,
    variant_id: str,
    current_user=Depends(require_permission("catalog.variants.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _variant_service(db, current_user)
    variant = await service.set_default_variant(variant_id)
    if variant.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found.")
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="Variant", entity_id=variant.id,
        user_id=current_user.id, after={"is_default": True}, context=audit_context,
    )
    return variant


@router.delete("/{variant_id}")
async def delete_variant(
    product_id: str,
    variant_id: str,
    current_user=Depends(require_permission("catalog.variants.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _variant_service(db, current_user)
    await service.delete_variant(variant_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="Variant", entity_id=variant_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Variant deleted successfully."}
