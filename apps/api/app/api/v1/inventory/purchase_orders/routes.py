from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.models.purchase_order import PurchaseOrderStatus as ModelPurchaseOrderStatus
from app.schemas.purchase_order import (
    BulkDeleteRequest,
    PurchaseOrderCreateRequest,
    PurchaseOrderDetail,
    PurchaseOrderLineItem,
    PurchaseOrderLineItemInput,
    PurchaseOrderListResponse,
    PurchaseOrderRead,
    PurchaseOrderUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.purchase_order_service import PurchaseOrderService

router = APIRouter(prefix="/purchase-orders", tags=["inventory-purchase-orders"])


def _po_service(db: AsyncSession, current_user) -> PurchaseOrderService:
    return PurchaseOrderService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=PurchaseOrderListResponse)
async def list_purchase_orders(
    warehouse_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    q: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("inventory.purchase_orders.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _po_service(db, current_user)
    model_status = ModelPurchaseOrderStatus(status_filter) if status_filter else None
    items, total = await service.list_purchase_orders(warehouse_id, model_status, q, sort_by, sort_order, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=PurchaseOrderRead, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    data: PurchaseOrderCreateRequest,
    current_user=Depends(require_permission("inventory.purchase_orders.create")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _po_service(db, current_user)
    purchase_order = await service.create_purchase_order(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="inventory", entity="PurchaseOrder", entity_id=purchase_order.id,
        user_id=current_user.id, after={"po_number": purchase_order.po_number, "total": purchase_order.total}, context=audit_context,
    )
    return purchase_order


@router.get("/{po_id}", response_model=PurchaseOrderDetail)
async def get_purchase_order(po_id: str, current_user=Depends(require_permission("inventory.purchase_orders.view")), db: AsyncSession = Depends(get_db)):
    service = _po_service(db, current_user)
    purchase_order = await service.get_purchase_order(po_id)
    if not purchase_order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found.")
    items = await service.get_items(po_id)
    detail = PurchaseOrderDetail.model_validate(purchase_order)
    detail.items = [PurchaseOrderLineItem.model_validate(item) for item in items]
    return detail


@router.patch("/{po_id}", response_model=PurchaseOrderRead)
async def update_purchase_order(
    po_id: str,
    data: PurchaseOrderUpdateRequest,
    current_user=Depends(require_permission("inventory.purchase_orders.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _po_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    purchase_order = await service.update_purchase_order(po_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="PurchaseOrder", entity_id=purchase_order.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return purchase_order


@router.delete("/{po_id}")
async def delete_purchase_order(
    po_id: str,
    current_user=Depends(require_permission("inventory.purchase_orders.delete")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _po_service(db, current_user)
    await service.delete_purchase_order(po_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="inventory", entity="PurchaseOrder", entity_id=po_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Purchase order deleted successfully."}


@router.post("/{po_id}/send", response_model=PurchaseOrderRead)
async def send_purchase_order(
    po_id: str,
    current_user=Depends(require_permission("inventory.purchase_orders.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _po_service(db, current_user)
    purchase_order = await service.send_purchase_order(po_id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="PurchaseOrder", entity_id=purchase_order.id,
        user_id=current_user.id, after={"status": "sent"}, context=audit_context,
    )
    return purchase_order


@router.post("/{po_id}/cancel", response_model=PurchaseOrderRead)
async def cancel_purchase_order(
    po_id: str,
    current_user=Depends(require_permission("inventory.purchase_orders.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _po_service(db, current_user)
    purchase_order = await service.cancel_purchase_order(po_id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="PurchaseOrder", entity_id=purchase_order.id,
        user_id=current_user.id, after={"status": "cancelled"}, context=audit_context,
    )
    return purchase_order


@router.get("/{po_id}/items", response_model=list[PurchaseOrderLineItem])
async def list_purchase_order_items(po_id: str, current_user=Depends(require_permission("inventory.purchase_orders.view")), db: AsyncSession = Depends(get_db)):
    service = _po_service(db, current_user)
    return await service.get_items(po_id)


@router.post("/{po_id}/items", response_model=PurchaseOrderLineItem, status_code=status.HTTP_201_CREATED)
async def add_purchase_order_item(
    po_id: str,
    data: PurchaseOrderLineItemInput,
    current_user=Depends(require_permission("inventory.purchase_orders.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _po_service(db, current_user)
    item = await service.add_item(po_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="PurchaseOrder", entity_id=po_id,
        user_id=current_user.id, after={"added_item": item.id}, context=audit_context,
    )
    return item


@router.delete("/{po_id}/items/{item_id}")
async def remove_purchase_order_item(
    po_id: str,
    item_id: str,
    current_user=Depends(require_permission("inventory.purchase_orders.edit")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _po_service(db, current_user)
    await service.remove_item(po_id, item_id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="PurchaseOrder", entity_id=po_id,
        user_id=current_user.id, after={"removed_item": item_id}, context=audit_context,
    )
    return {"detail": "Purchase order item removed."}
