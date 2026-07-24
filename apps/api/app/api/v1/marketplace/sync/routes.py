from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.schemas.marketplace_sync_log import MarketplaceSyncLogListResponse, MarketplaceSyncLogRead
from app.repositories.marketplace_sync_log_repository import MarketplaceSyncLogRepository
from app.services.audit_service import AuditService
from app.services.marketplace_sync_service import MarketplaceSyncService

router = APIRouter(prefix="/sync", tags=["marketplace-sync"])


class SyncProductsRequest(BaseModel):
    product_ids: list[str] | None = None


def _service(db: AsyncSession, current_user) -> MarketplaceSyncService:
    return MarketplaceSyncService(db, current_user.organization_id, current_user.is_superuser)


async def _audit_sync(db: AsyncSession, current_user, audit_context: AuditContext, connector_id: str, sync_type: str, log) -> None:
    await AuditService(db, current_user.organization_id).log(
        action="sync", module="marketplace", entity="MarketplaceConnector", entity_id=connector_id,
        user_id=current_user.id,
        after={"sync_type": sync_type, "status": log.status.value, "items_processed": log.items_processed, "items_failed": log.items_failed},
        context=audit_context,
    )


@router.post("/{connector_id}/products", response_model=MarketplaceSyncLogRead)
async def sync_marketplace_products(
    connector_id: str,
    data: SyncProductsRequest = SyncProductsRequest(),
    current_user=Depends(require_permission("marketplace.sync.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _service(db, current_user)
    log = await service.sync_products(connector_id, data.product_ids, triggered_by="manual")
    await _audit_sync(db, current_user, audit_context, connector_id, "product", log)
    return log


@router.post("/{connector_id}/inventory", response_model=MarketplaceSyncLogRead)
async def sync_marketplace_inventory(
    connector_id: str,
    data: SyncProductsRequest = SyncProductsRequest(),
    current_user=Depends(require_permission("marketplace.sync.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _service(db, current_user)
    log = await service.sync_inventory(connector_id, data.product_ids, triggered_by="manual")
    await _audit_sync(db, current_user, audit_context, connector_id, "inventory", log)
    return log


@router.post("/{connector_id}/prices", response_model=MarketplaceSyncLogRead)
async def sync_marketplace_prices(
    connector_id: str,
    data: SyncProductsRequest = SyncProductsRequest(),
    current_user=Depends(require_permission("marketplace.sync.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _service(db, current_user)
    log = await service.sync_prices(connector_id, data.product_ids, triggered_by="manual")
    await _audit_sync(db, current_user, audit_context, connector_id, "price", log)
    return log


@router.post("/{connector_id}/orders", response_model=MarketplaceSyncLogRead)
async def sync_marketplace_orders(
    connector_id: str,
    current_user=Depends(require_permission("marketplace.sync.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _service(db, current_user)
    log = await service.sync_orders(connector_id, triggered_by="manual")
    await _audit_sync(db, current_user, audit_context, connector_id, "order", log)
    return log


@router.get("/logs", response_model=MarketplaceSyncLogListResponse)
async def list_marketplace_sync_logs(
    connector_id: str | None = Query(None),
    sync_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("marketplace.sync.view")),
    db: AsyncSession = Depends(get_db),
):
    repo = MarketplaceSyncLogRepository(db, current_user.organization_id, current_user.is_superuser)
    items = await repo.list(connector_id, sync_type, limit, offset)
    total = await repo.count(connector_id, sync_type)
    return {"items": items, "total": total, "limit": limit, "offset": offset}
