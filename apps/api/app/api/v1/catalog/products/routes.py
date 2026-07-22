from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_current_active_user, get_db, require_permission
from app.models.product import ProductStatus as ModelProductStatus
from app.schemas.product import (
    BulkDeleteRequest,
    BulkStatusUpdateRequest,
    ProductCreateRequest,
    ProductItem,
    ProductListResponse,
    ProductStatus,
    ProductUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["catalog-products"])


def _product_service(db: AsyncSession, current_user) -> ProductService:
    return ProductService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=ProductListResponse)
async def list_products(
    status_filter: ProductStatus | None = Query(None, alias="status"),
    brand_id: str | None = Query(None),
    category_id: str | None = Query(None),
    is_featured: bool | None = Query(None),
    has_variants: bool | None = Query(None),
    tag_id: str | None = Query(None),
    q: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("catalog.products.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _product_service(db, current_user)
    model_status = ModelProductStatus(status_filter.value) if status_filter else None
    items, total = await service.list_products(
        model_status, brand_id, category_id, is_featured, has_variants, q, sort_by, sort_order, limit, offset, tag_id,
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=ProductItem, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreateRequest,
    current_user=Depends(require_permission("catalog.products.create")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _product_service(db, current_user)
    product = await service.create_product(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="catalog", entity="Product", entity_id=product.id,
        user_id=current_user.id, after={"name": product.name, "sku": product.sku, "status": product.status.value}, context=audit_context,
    )
    return product


@router.post("/bulk-delete")
async def bulk_delete_products(
    data: BulkDeleteRequest,
    current_user=Depends(require_permission("catalog.products.delete")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _product_service(db, current_user)
    deleted_count = await service.bulk_delete(data.ids)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="Product", user_id=current_user.id,
        before={"ids": data.ids}, after={"deleted_count": deleted_count}, context=audit_context,
    )
    return {"deleted_count": deleted_count}


@router.post("/bulk-status")
async def bulk_update_product_status(
    data: BulkStatusUpdateRequest,
    current_user=Depends(require_permission("catalog.products.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _product_service(db, current_user)
    model_status = ModelProductStatus(data.status.value)
    updated_count = await service.bulk_update_status(data.ids, model_status)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="Product", user_id=current_user.id,
        before={"ids": data.ids}, after={"status": data.status.value, "updated_count": updated_count}, context=audit_context,
    )
    return {"updated_count": updated_count}


@router.get("/{product_id}", response_model=ProductItem)
async def get_product(product_id: str, current_user=Depends(require_permission("catalog.products.view")), db: AsyncSession = Depends(get_db)):
    service = _product_service(db, current_user)
    product = await service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product


@router.patch("/{product_id}", response_model=ProductItem)
async def update_product(
    product_id: str,
    data: ProductUpdateRequest,
    current_user=Depends(require_permission("catalog.products.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _product_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    product = await service.update_product(product_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="Product", entity_id=product.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return product


@router.post("/{product_id}/publish", response_model=ProductItem)
async def publish_product(
    product_id: str,
    current_user=Depends(require_permission("catalog.products.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _product_service(db, current_user)
    product = await service.publish_product(product_id, current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="publish", module="catalog", entity="Product", entity_id=product.id,
        user_id=current_user.id, context=audit_context,
    )
    return product


@router.post("/{product_id}/archive", response_model=ProductItem)
async def archive_product(
    product_id: str,
    current_user=Depends(require_permission("catalog.products.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _product_service(db, current_user)
    product = await service.archive_product(product_id)
    await AuditService(db, current_user.organization_id).log(
        action="archive", module="catalog", entity="Product", entity_id=product.id,
        user_id=current_user.id, context=audit_context,
    )
    return product


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    current_user=Depends(require_permission("catalog.products.delete")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _product_service(db, current_user)
    await service.delete_product(product_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="Product", entity_id=product_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Product deleted successfully."}


@router.post("/{product_id}/restore", response_model=ProductItem)
async def restore_product(
    product_id: str,
    current_user=Depends(require_permission("catalog.products.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _product_service(db, current_user)
    product = await service.restore_product(product_id)
    await AuditService(db, current_user.organization_id).log(
        action="restore", module="catalog", entity="Product", entity_id=product.id,
        user_id=current_user.id, context=audit_context,
    )
    return product
