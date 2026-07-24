from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.schemas.marketplace_connector import (
    MarketplaceConnectorCreateRequest,
    MarketplaceConnectorListResponse,
    MarketplaceConnectorRead,
    MarketplaceConnectorUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.marketplace_connector_service import MarketplaceConnectorService

router = APIRouter(prefix="/connectors", tags=["marketplace-connectors"])


def _service(db: AsyncSession, current_user) -> MarketplaceConnectorService:
    return MarketplaceConnectorService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=MarketplaceConnectorListResponse)
async def list_marketplace_connectors(
    is_active: bool | None = Query(None),
    connector_type: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("marketplace.connectors.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _service(db, current_user)
    items, total = await service.list_connectors(is_active, connector_type, sort_by, sort_order, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=MarketplaceConnectorRead, status_code=status.HTTP_201_CREATED)
async def create_marketplace_connector(
    data: MarketplaceConnectorCreateRequest,
    current_user=Depends(require_permission("marketplace.connectors.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _service(db, current_user)
    connector = await service.create_connector(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="marketplace", entity="MarketplaceConnector", entity_id=connector.id,
        user_id=current_user.id, after={"code": connector.code, "connector_type": connector.connector_type}, context=audit_context,
    )
    return connector


@router.get("/{connector_id}", response_model=MarketplaceConnectorRead)
async def get_marketplace_connector(connector_id: str, current_user=Depends(require_permission("marketplace.connectors.view")), db: AsyncSession = Depends(get_db)):
    service = _service(db, current_user)
    connector = await service.get_connector(connector_id)
    if not connector:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marketplace connector not found.")
    return connector


@router.patch("/{connector_id}", response_model=MarketplaceConnectorRead)
async def update_marketplace_connector(
    connector_id: str,
    data: MarketplaceConnectorUpdateRequest,
    current_user=Depends(require_permission("marketplace.connectors.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _service(db, current_user)
    changes = data.model_dump(exclude_unset=True, exclude={"credentials"})
    connector = await service.update_connector(connector_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="marketplace", entity="MarketplaceConnector", entity_id=connector.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return connector


@router.delete("/{connector_id}")
async def delete_marketplace_connector(
    connector_id: str,
    current_user=Depends(require_permission("marketplace.connectors.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _service(db, current_user)
    await service.delete_connector(connector_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="marketplace", entity="MarketplaceConnector", entity_id=connector_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Marketplace connector deleted successfully."}
