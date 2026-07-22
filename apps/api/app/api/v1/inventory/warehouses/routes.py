from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.models.warehouse import WarehouseType as ModelWarehouseType
from app.schemas.warehouse import (
    BulkDeleteRequest,
    WarehouseBinCreateRequest,
    WarehouseBinItem,
    WarehouseBinListResponse,
    WarehouseBinUpdateRequest,
    WarehouseCreateRequest,
    WarehouseItem,
    WarehouseListResponse,
    WarehouseUpdateRequest,
    WarehouseZoneCreateRequest,
    WarehouseZoneItem,
    WarehouseZoneListResponse,
    WarehouseZoneUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.warehouse_service import WarehouseService

router = APIRouter(prefix="/warehouses", tags=["inventory-warehouses"])


def _warehouse_service(db: AsyncSession, current_user) -> WarehouseService:
    return WarehouseService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=WarehouseListResponse)
async def list_warehouses(
    warehouse_type: str | None = Query(None, alias="type"),
    is_active: bool | None = Query(None),
    q: str | None = Query(None),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("inventory.warehouses.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _warehouse_service(db, current_user)
    model_type = ModelWarehouseType(warehouse_type) if warehouse_type else None
    items, total = await service.list_warehouses(model_type, is_active, q, sort_by, sort_order, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=WarehouseItem, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    data: WarehouseCreateRequest,
    current_user=Depends(require_permission("inventory.warehouses.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _warehouse_service(db, current_user)
    warehouse = await service.create_warehouse(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="inventory", entity="Warehouse", entity_id=warehouse.id,
        user_id=current_user.id, after={"name": warehouse.name, "code": warehouse.code}, context=audit_context,
    )
    return warehouse


@router.post("/bulk-delete")
async def bulk_delete_warehouses(
    data: BulkDeleteRequest,
    current_user=Depends(require_permission("inventory.warehouses.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _warehouse_service(db, current_user)
    deleted_count = await service.bulk_delete(data.ids)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="inventory", entity="Warehouse", user_id=current_user.id,
        before={"ids": data.ids}, after={"deleted_count": deleted_count}, context=audit_context,
    )
    return {"deleted_count": deleted_count}


@router.get("/{warehouse_id}", response_model=WarehouseItem)
async def get_warehouse(warehouse_id: str, current_user=Depends(require_permission("inventory.warehouses.view")), db: AsyncSession = Depends(get_db)):
    service = _warehouse_service(db, current_user)
    warehouse = await service.get_warehouse(warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found.")
    return warehouse


@router.patch("/{warehouse_id}", response_model=WarehouseItem)
async def update_warehouse(
    warehouse_id: str,
    data: WarehouseUpdateRequest,
    current_user=Depends(require_permission("inventory.warehouses.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _warehouse_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    warehouse = await service.update_warehouse(warehouse_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="Warehouse", entity_id=warehouse.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return warehouse


@router.delete("/{warehouse_id}")
async def delete_warehouse(
    warehouse_id: str,
    current_user=Depends(require_permission("inventory.warehouses.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _warehouse_service(db, current_user)
    await service.delete_warehouse(warehouse_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="inventory", entity="Warehouse", entity_id=warehouse_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Warehouse deleted successfully."}


@router.post("/{warehouse_id}/restore", response_model=WarehouseItem)
async def restore_warehouse(
    warehouse_id: str,
    current_user=Depends(require_permission("inventory.warehouses.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _warehouse_service(db, current_user)
    warehouse = await service.restore_warehouse(warehouse_id)
    await AuditService(db, current_user.organization_id).log(
        action="restore", module="inventory", entity="Warehouse", entity_id=warehouse.id,
        user_id=current_user.id, context=audit_context,
    )
    return warehouse


@router.post("/{warehouse_id}/default", response_model=WarehouseItem)
async def set_default_warehouse(
    warehouse_id: str,
    current_user=Depends(require_permission("inventory.warehouses.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _warehouse_service(db, current_user)
    warehouse = await service.set_default(warehouse_id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="Warehouse", entity_id=warehouse.id,
        user_id=current_user.id, after={"is_default": True}, context=audit_context,
    )
    return warehouse


# --- Zones (nested under a warehouse) ---

@router.get("/{warehouse_id}/zones", response_model=WarehouseZoneListResponse)
async def list_zones(
    warehouse_id: str,
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("inventory.warehouses.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _warehouse_service(db, current_user)
    items, total = await service.list_zones(warehouse_id, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/{warehouse_id}/zones", response_model=WarehouseZoneItem, status_code=status.HTTP_201_CREATED)
async def create_zone(
    warehouse_id: str,
    data: WarehouseZoneCreateRequest,
    current_user=Depends(require_permission("inventory.warehouses.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _warehouse_service(db, current_user)
    zone = await service.create_zone(warehouse_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="inventory", entity="WarehouseZone", entity_id=zone.id,
        user_id=current_user.id, after={"name": zone.name, "code": zone.code}, context=audit_context,
    )
    return zone


@router.patch("/{warehouse_id}/zones/{zone_id}", response_model=WarehouseZoneItem)
async def update_zone(
    warehouse_id: str,
    zone_id: str,
    data: WarehouseZoneUpdateRequest,
    current_user=Depends(require_permission("inventory.warehouses.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _warehouse_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    zone = await service.update_zone(warehouse_id, zone_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="WarehouseZone", entity_id=zone.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return zone


@router.delete("/{warehouse_id}/zones/{zone_id}")
async def delete_zone(
    warehouse_id: str,
    zone_id: str,
    current_user=Depends(require_permission("inventory.warehouses.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _warehouse_service(db, current_user)
    await service.delete_zone(warehouse_id, zone_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="inventory", entity="WarehouseZone", entity_id=zone_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Warehouse zone deleted successfully."}


# --- Bins (nested under a warehouse) ---

@router.get("/{warehouse_id}/bins", response_model=WarehouseBinListResponse)
async def list_bins(
    warehouse_id: str,
    zone_id: str | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("inventory.warehouses.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _warehouse_service(db, current_user)
    items, total = await service.list_bins(warehouse_id, zone_id, q, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/{warehouse_id}/bins", response_model=WarehouseBinItem, status_code=status.HTTP_201_CREATED)
async def create_bin(
    warehouse_id: str,
    data: WarehouseBinCreateRequest,
    current_user=Depends(require_permission("inventory.warehouses.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _warehouse_service(db, current_user)
    bin_ = await service.create_bin(warehouse_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="inventory", entity="WarehouseBin", entity_id=bin_.id,
        user_id=current_user.id, after={"code": bin_.code}, context=audit_context,
    )
    return bin_


@router.patch("/{warehouse_id}/bins/{bin_id}", response_model=WarehouseBinItem)
async def update_bin(
    warehouse_id: str,
    bin_id: str,
    data: WarehouseBinUpdateRequest,
    current_user=Depends(require_permission("inventory.warehouses.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _warehouse_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    bin_ = await service.update_bin(warehouse_id, bin_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="WarehouseBin", entity_id=bin_.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return bin_


@router.delete("/{warehouse_id}/bins/{bin_id}")
async def delete_bin(
    warehouse_id: str,
    bin_id: str,
    current_user=Depends(require_permission("inventory.warehouses.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _warehouse_service(db, current_user)
    await service.delete_bin(warehouse_id, bin_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="inventory", entity="WarehouseBin", entity_id=bin_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Warehouse bin deleted successfully."}
