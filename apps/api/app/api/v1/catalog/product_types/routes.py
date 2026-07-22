from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_current_active_user, get_db, require_permission
from app.schemas.product_type import (
    ProductTypeAttributeItem,
    ProductTypeAttributesRequest,
    ProductTypeCreateRequest,
    ProductTypeItem,
    ProductTypeListResponse,
    ProductTypeUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.product_type_service import ProductTypeService

router = APIRouter(prefix="/product-types", tags=["catalog-product-types"])


def _product_type_service(db: AsyncSession, current_user) -> ProductTypeService:
    return ProductTypeService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=ProductTypeListResponse)
async def list_product_types(
    is_active: bool | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("catalog.products.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _product_type_service(db, current_user)
    items, total = await service.list_product_types(is_active, q, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=ProductTypeItem, status_code=status.HTTP_201_CREATED)
async def create_product_type(
    data: ProductTypeCreateRequest,
    current_user=Depends(require_permission("catalog.product_types.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _product_type_service(db, current_user)
    product_type = await service.create_product_type(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="catalog", entity="ProductType", entity_id=product_type.id,
        user_id=current_user.id, after={"name": product_type.name, "slug": product_type.slug}, context=audit_context,
    )
    return product_type


@router.get("/{product_type_id}", response_model=ProductTypeItem)
async def get_product_type(product_type_id: str, current_user=Depends(require_permission("catalog.products.view")), db: AsyncSession = Depends(get_db)):
    service = _product_type_service(db, current_user)
    product_type = await service.get_product_type(product_type_id)
    if not product_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product type not found.")
    return product_type


@router.patch("/{product_type_id}", response_model=ProductTypeItem)
async def update_product_type(
    product_type_id: str,
    data: ProductTypeUpdateRequest,
    current_user=Depends(require_permission("catalog.product_types.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _product_type_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    product_type = await service.update_product_type(product_type_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="ProductType", entity_id=product_type.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return product_type


@router.delete("/{product_type_id}")
async def delete_product_type(
    product_type_id: str,
    current_user=Depends(require_permission("catalog.product_types.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _product_type_service(db, current_user)
    await service.delete_product_type(product_type_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="ProductType", entity_id=product_type_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Product type deleted successfully."}


@router.get("/{product_type_id}/attributes", response_model=list[ProductTypeAttributeItem])
async def get_product_type_attributes(product_type_id: str, current_user=Depends(require_permission("catalog.products.view")), db: AsyncSession = Depends(get_db)):
    service = _product_type_service(db, current_user)
    return await service.get_attributes(product_type_id)


@router.put("/{product_type_id}/attributes")
async def set_product_type_attributes(
    product_type_id: str,
    data: ProductTypeAttributesRequest,
    current_user=Depends(require_permission("catalog.product_types.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _product_type_service(db, current_user)
    await service.set_attributes(product_type_id, data.attributes)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="ProductType", entity_id=product_type_id,
        user_id=current_user.id, after={"attribute_count": len(data.attributes)}, context=audit_context,
    )
    return {"detail": "Product type attributes updated."}
