from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_current_active_user, get_db, require_permission
from app.models.category import CategoryStatus as ModelCategoryStatus
from app.schemas.category import (
    CategoryBreadcrumbItem,
    CategoryCreateRequest,
    CategoryItem,
    CategoryListResponse,
    CategoryStatus,
    CategoryTreeNode,
    CategoryUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["catalog-categories"])


def _category_service(db: AsyncSession, current_user) -> CategoryService:
    return CategoryService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=CategoryListResponse)
async def list_categories(
    parent_id: str | None = Query(None),
    root_only: bool = Query(False, description="If true, only return top-level categories."),
    status_filter: CategoryStatus | None = Query(None, alias="status"),
    is_featured: bool | None = Query(None),
    is_visible: bool | None = Query(None),
    q: str | None = Query(None),
    sort_by: str = Query("sort_order"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("catalog.categories.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _category_service(db, current_user)
    resolved_parent_id = parent_id if (parent_id is not None or root_only) else "__unset__"
    model_status = ModelCategoryStatus(status_filter.value) if status_filter else None
    items, total = await service.list_categories(
        parent_id=resolved_parent_id,
        status_filter=model_status,
        is_featured=is_featured,
        is_visible=is_visible,
        q=q,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/tree", response_model=list[CategoryTreeNode])
async def get_category_tree(
    parent_id: str | None = Query(None),
    current_user=Depends(require_permission("catalog.categories.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _category_service(db, current_user)
    return await service.get_tree(parent_id)


@router.post("/", response_model=CategoryItem, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreateRequest,
    current_user=Depends(require_permission("catalog.categories.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _category_service(db, current_user)
    category = await service.create_category(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create",
        module="catalog",
        entity="Category",
        entity_id=category.id,
        user_id=current_user.id,
        after={"name": category.name, "slug": category.slug, "parent_id": category.parent_id},
        context=audit_context,
    )
    return category


@router.get("/{category_id}", response_model=CategoryItem)
async def get_category(
    category_id: str,
    current_user=Depends(require_permission("catalog.categories.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _category_service(db, current_user)
    category = await service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
    return category


@router.get("/{category_id}/breadcrumbs", response_model=list[CategoryBreadcrumbItem])
async def get_breadcrumbs(
    category_id: str,
    current_user=Depends(require_permission("catalog.categories.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _category_service(db, current_user)
    return await service.get_breadcrumbs(category_id)


@router.get("/{category_id}/children", response_model=list[CategoryItem])
async def list_children(
    category_id: str,
    current_user=Depends(require_permission("catalog.categories.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _category_service(db, current_user)
    return await service.repo.list_children(category_id)


@router.patch("/{category_id}", response_model=CategoryItem)
async def update_category(
    category_id: str,
    data: CategoryUpdateRequest,
    current_user=Depends(require_permission("catalog.categories.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _category_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    category = await service.update_category(category_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update",
        module="catalog",
        entity="Category",
        entity_id=category.id,
        user_id=current_user.id,
        after=changes,
        context=audit_context,
    )
    return category


@router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    cascade: bool = Query(False),
    current_user=Depends(require_permission("catalog.categories.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _category_service(db, current_user)
    await service.delete_category(category_id, cascade=cascade)
    await AuditService(db, current_user.organization_id).log(
        action="delete",
        module="catalog",
        entity="Category",
        entity_id=category_id,
        user_id=current_user.id,
        before={"cascade": cascade},
        context=audit_context,
    )
    return {"detail": "Category deleted successfully."}


@router.post("/{category_id}/restore", response_model=CategoryItem)
async def restore_category(
    category_id: str,
    current_user=Depends(require_permission("catalog.categories.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _category_service(db, current_user)
    category = await service.restore_category(category_id)
    await AuditService(db, current_user.organization_id).log(
        action="restore",
        module="catalog",
        entity="Category",
        entity_id=category.id,
        user_id=current_user.id,
        context=audit_context,
    )
    return category
