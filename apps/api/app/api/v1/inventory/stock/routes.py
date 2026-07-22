from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.models.inventory_transaction import InventoryTransactionType as ModelTransactionType
from app.schemas.inventory import (
    InventoryItem,
    InventoryListResponse,
    InventoryTransactionListResponse,
    InventoryUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/stock", tags=["inventory-stock"])


def _inventory_service(db: AsyncSession, current_user) -> InventoryService:
    return InventoryService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=InventoryListResponse)
async def list_inventory(
    warehouse_id: str | None = Query(None),
    product_id: str | None = Query(None),
    low_stock_only: bool = Query(False),
    sort_by: str = Query("updated_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("inventory.stock.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _inventory_service(db, current_user)
    items, total = await service.list_inventory(warehouse_id, product_id, low_stock_only, sort_by, sort_order, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/transactions", response_model=InventoryTransactionListResponse)
async def list_inventory_transactions(
    inventory_id: str | None = Query(None),
    warehouse_id: str | None = Query(None),
    product_id: str | None = Query(None),
    type_filter: str | None = Query(None, alias="type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("inventory.stock.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _inventory_service(db, current_user)
    model_type = ModelTransactionType(type_filter) if type_filter else None
    items, total = await service.list_transactions(inventory_id, warehouse_id, product_id, model_type, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/{inventory_id}", response_model=InventoryItem)
async def get_inventory(inventory_id: str, current_user=Depends(require_permission("inventory.stock.view")), db: AsyncSession = Depends(get_db)):
    service = _inventory_service(db, current_user)
    inventory = await service.get_inventory(inventory_id)
    if not inventory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory record not found.")
    return inventory


@router.patch("/{inventory_id}", response_model=InventoryItem)
async def update_inventory(
    inventory_id: str,
    data: InventoryUpdateRequest,
    current_user=Depends(require_permission("inventory.stock.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _inventory_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    inventory = await service.update_inventory(inventory_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="Inventory", entity_id=inventory.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return inventory
