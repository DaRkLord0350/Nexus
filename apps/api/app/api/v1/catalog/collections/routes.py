from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_current_active_user, get_db, require_permission
from app.models.collection import CollectionStatus as ModelCollectionStatus
from app.schemas.collection import (
    BulkDeleteRequest,
    CollectionCreateRequest,
    CollectionItem,
    CollectionListResponse,
    CollectionProductsRequest,
    CollectionStatus,
    CollectionUpdateRequest,
)
from app.schemas.product import ProductItem
from app.services.audit_service import AuditService
from app.services.collection_service import CollectionService

router = APIRouter(prefix="/collections", tags=["catalog-collections"])


def _collection_service(db: AsyncSession, current_user) -> CollectionService:
    return CollectionService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=CollectionListResponse)
async def list_collections(
    status_filter: CollectionStatus | None = Query(None, alias="status"),
    is_featured: bool | None = Query(None),
    q: str | None = Query(None),
    sort_by: str = Query("sort_order"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("catalog.collections.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _collection_service(db, current_user)
    model_status = ModelCollectionStatus(status_filter.value) if status_filter else None
    items, total = await service.list_collections(model_status, is_featured, q, sort_by, sort_order, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=CollectionItem, status_code=status.HTTP_201_CREATED)
async def create_collection(
    data: CollectionCreateRequest,
    current_user=Depends(require_permission("catalog.collections.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _collection_service(db, current_user)
    collection = await service.create_collection(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="catalog", entity="Collection", entity_id=collection.id,
        user_id=current_user.id, after={"name": collection.name, "collection_type": collection.collection_type.value}, context=audit_context,
    )
    return collection


@router.post("/bulk-delete")
async def bulk_delete_collections(
    data: BulkDeleteRequest,
    current_user=Depends(require_permission("catalog.collections.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _collection_service(db, current_user)
    deleted_count = await service.bulk_delete(data.ids)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="Collection", user_id=current_user.id,
        before={"ids": data.ids}, after={"deleted_count": deleted_count}, context=audit_context,
    )
    return {"deleted_count": deleted_count}


@router.get("/{collection_id}", response_model=CollectionItem)
async def get_collection(collection_id: str, current_user=Depends(require_permission("catalog.collections.view")), db: AsyncSession = Depends(get_db)):
    service = _collection_service(db, current_user)
    collection = await service.get_collection(collection_id)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")
    return collection


@router.get("/{collection_id}/products", response_model=list[ProductItem])
async def get_collection_products(collection_id: str, current_user=Depends(require_permission("catalog.collections.view")), db: AsyncSession = Depends(get_db)):
    service = _collection_service(db, current_user)
    return await service.get_products(collection_id)


@router.post("/{collection_id}/products")
async def add_collection_products(
    collection_id: str,
    data: CollectionProductsRequest,
    current_user=Depends(require_permission("catalog.collections.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _collection_service(db, current_user)
    await service.add_products(collection_id, data.product_ids)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="Collection", entity_id=collection_id,
        user_id=current_user.id, after={"added_product_ids": data.product_ids}, context=audit_context,
    )
    return {"detail": "Products added to collection."}


@router.delete("/{collection_id}/products")
async def remove_collection_products(
    collection_id: str,
    data: CollectionProductsRequest,
    current_user=Depends(require_permission("catalog.collections.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _collection_service(db, current_user)
    await service.remove_products(collection_id, data.product_ids)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="Collection", entity_id=collection_id,
        user_id=current_user.id, after={"removed_product_ids": data.product_ids}, context=audit_context,
    )
    return {"detail": "Products removed from collection."}


@router.post("/{collection_id}/products/reorder")
async def reorder_collection_products(
    collection_id: str,
    data: CollectionProductsRequest,
    current_user=Depends(require_permission("catalog.collections.manage")),
    db: AsyncSession = Depends(get_db),
):
    service = _collection_service(db, current_user)
    await service.reorder_products(collection_id, data.product_ids)
    return {"detail": "Collection products reordered."}


@router.patch("/{collection_id}", response_model=CollectionItem)
async def update_collection(
    collection_id: str,
    data: CollectionUpdateRequest,
    current_user=Depends(require_permission("catalog.collections.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _collection_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    collection = await service.update_collection(collection_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="Collection", entity_id=collection.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return collection


@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: str,
    current_user=Depends(require_permission("catalog.collections.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _collection_service(db, current_user)
    await service.delete_collection(collection_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="Collection", entity_id=collection_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Collection deleted successfully."}


@router.post("/{collection_id}/restore", response_model=CollectionItem)
async def restore_collection(
    collection_id: str,
    current_user=Depends(require_permission("catalog.collections.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _collection_service(db, current_user)
    collection = await service.restore_collection(collection_id)
    await AuditService(db, current_user.organization_id).log(
        action="restore", module="catalog", entity="Collection", entity_id=collection.id,
        user_id=current_user.id, context=audit_context,
    )
    return collection
