from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_current_active_user, get_db, require_permission
from app.models.brand import BrandStatus as ModelBrandStatus
from app.schemas.brand import (
    BrandCreateRequest,
    BrandItem,
    BrandListResponse,
    BrandStatus,
    BrandUpdateRequest,
    BulkDeleteRequest,
)
from app.services.audit_service import AuditService
from app.services.brand_service import BrandService

router = APIRouter(prefix="/brands", tags=["catalog-brands"])


def _brand_service(db: AsyncSession, current_user) -> BrandService:
    return BrandService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=BrandListResponse)
async def list_brands(
    status_filter: BrandStatus | None = Query(None, alias="status"),
    is_featured: bool | None = Query(None),
    q: str | None = Query(None),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("catalog.brands.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _brand_service(db, current_user)
    model_status = ModelBrandStatus(status_filter.value) if status_filter else None
    items, total = await service.list_brands(model_status, is_featured, q, sort_by, sort_order, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=BrandItem, status_code=status.HTTP_201_CREATED)
async def create_brand(
    data: BrandCreateRequest,
    current_user=Depends(require_permission("catalog.brands.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _brand_service(db, current_user)
    brand = await service.create_brand(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="catalog", entity="Brand", entity_id=brand.id,
        user_id=current_user.id, after={"name": brand.name, "slug": brand.slug}, context=audit_context,
    )
    return brand


@router.post("/bulk-delete")
async def bulk_delete_brands(
    data: BulkDeleteRequest,
    current_user=Depends(require_permission("catalog.brands.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _brand_service(db, current_user)
    deleted_count = await service.bulk_delete(data.ids)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="Brand", user_id=current_user.id,
        before={"ids": data.ids}, after={"deleted_count": deleted_count}, context=audit_context,
    )
    return {"deleted_count": deleted_count}


@router.get("/{brand_id}", response_model=BrandItem)
async def get_brand(brand_id: str, current_user=Depends(require_permission("catalog.brands.view")), db: AsyncSession = Depends(get_db)):
    service = _brand_service(db, current_user)
    brand = await service.get_brand(brand_id)
    if not brand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found.")
    return brand


@router.patch("/{brand_id}", response_model=BrandItem)
async def update_brand(
    brand_id: str,
    data: BrandUpdateRequest,
    current_user=Depends(require_permission("catalog.brands.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _brand_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    brand = await service.update_brand(brand_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="Brand", entity_id=brand.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return brand


@router.delete("/{brand_id}")
async def delete_brand(
    brand_id: str,
    current_user=Depends(require_permission("catalog.brands.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _brand_service(db, current_user)
    await service.delete_brand(brand_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="Brand", entity_id=brand_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Brand deleted successfully."}


@router.post("/{brand_id}/restore", response_model=BrandItem)
async def restore_brand(
    brand_id: str,
    current_user=Depends(require_permission("catalog.brands.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _brand_service(db, current_user)
    brand = await service.restore_brand(brand_id)
    await AuditService(db, current_user.organization_id).log(
        action="restore", module="catalog", entity="Brand", entity_id=brand.id,
        user_id=current_user.id, context=audit_context,
    )
    return brand
