from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_current_active_user, get_db, require_permission
from app.schemas.channel import (
    ChannelCreateRequest,
    ChannelItem,
    ChannelListResponse,
    ChannelUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.channel_service import ChannelService

router = APIRouter(prefix="/channels", tags=["catalog-channels"])


def _channel_service(db: AsyncSession, current_user) -> ChannelService:
    return ChannelService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=ChannelListResponse)
async def list_channels(
    is_active: bool | None = Query(None),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("catalog.products.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _channel_service(db, current_user)
    items, total = await service.list_channels(is_active, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=ChannelItem, status_code=status.HTTP_201_CREATED)
async def create_channel(
    data: ChannelCreateRequest,
    current_user=Depends(require_permission("catalog.channels.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _channel_service(db, current_user)
    channel = await service.create_channel(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="catalog", entity="Channel", entity_id=channel.id,
        user_id=current_user.id, after={"name": channel.name, "code": channel.code}, context=audit_context,
    )
    return channel


@router.get("/{channel_id}", response_model=ChannelItem)
async def get_channel(channel_id: str, current_user=Depends(require_permission("catalog.products.view")), db: AsyncSession = Depends(get_db)):
    service = _channel_service(db, current_user)
    channel = await service.get_channel(channel_id)
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found.")
    return channel


@router.patch("/{channel_id}", response_model=ChannelItem)
async def update_channel(
    channel_id: str,
    data: ChannelUpdateRequest,
    current_user=Depends(require_permission("catalog.channels.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _channel_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    channel = await service.update_channel(channel_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="Channel", entity_id=channel.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return channel


@router.delete("/{channel_id}")
async def delete_channel(
    channel_id: str,
    current_user=Depends(require_permission("catalog.channels.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _channel_service(db, current_user)
    await service.delete_channel(channel_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="Channel", entity_id=channel_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Channel deleted successfully."}
