from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_current_active_user, get_db, require_permission
from app.schemas.tag import TagCreateRequest, TagItem, TagListResponse, TagUpdateRequest
from app.services.audit_service import AuditService
from app.services.tag_service import TagService

router = APIRouter(prefix="/tags", tags=["catalog-tags"])


def _tag_service(db: AsyncSession, current_user) -> TagService:
    return TagService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=TagListResponse)
async def list_tags(
    q: str | None = Query(None),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("catalog.products.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _tag_service(db, current_user)
    items, total = await service.list_tags(q, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=TagItem, status_code=status.HTTP_201_CREATED)
async def create_tag(
    data: TagCreateRequest,
    current_user=Depends(require_permission("catalog.tags.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _tag_service(db, current_user)
    tag = await service.create_tag(data)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="catalog", entity="Tag", entity_id=tag.id,
        user_id=current_user.id, after={"name": tag.name, "slug": tag.slug}, context=audit_context,
    )
    return tag


@router.get("/{tag_id}", response_model=TagItem)
async def get_tag(tag_id: str, current_user=Depends(require_permission("catalog.products.view")), db: AsyncSession = Depends(get_db)):
    service = _tag_service(db, current_user)
    tag = await service.get_tag(tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found.")
    return tag


@router.patch("/{tag_id}", response_model=TagItem)
async def update_tag(
    tag_id: str,
    data: TagUpdateRequest,
    current_user=Depends(require_permission("catalog.tags.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _tag_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    tag = await service.update_tag(tag_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="Tag", entity_id=tag.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return tag


@router.delete("/{tag_id}")
async def delete_tag(
    tag_id: str,
    current_user=Depends(require_permission("catalog.tags.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _tag_service(db, current_user)
    await service.delete_tag(tag_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="Tag", entity_id=tag_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Tag deleted successfully."}
