from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.models.goods_receipt import GoodsReceiptStatus as ModelGoodsReceiptStatus
from app.schemas.goods_receipt import (
    GoodsReceiptCreateRequest,
    GoodsReceiptDetail,
    GoodsReceiptItemInput,
    GoodsReceiptLineItem,
    GoodsReceiptListResponse,
    GoodsReceiptRead,
)
from app.services.audit_service import AuditService
from app.services.goods_receipt_service import GoodsReceiptService

router = APIRouter(prefix="/goods-receipts", tags=["inventory-goods-receipts"])


def _receipt_service(db: AsyncSession, current_user) -> GoodsReceiptService:
    return GoodsReceiptService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=GoodsReceiptListResponse)
async def list_goods_receipts(
    warehouse_id: str | None = Query(None),
    purchase_order_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    q: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("inventory.goods_receipts.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _receipt_service(db, current_user)
    model_status = ModelGoodsReceiptStatus(status_filter) if status_filter else None
    items, total = await service.list_receipts(warehouse_id, purchase_order_id, model_status, q, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=GoodsReceiptRead, status_code=status.HTTP_201_CREATED)
async def create_goods_receipt(
    data: GoodsReceiptCreateRequest,
    current_user=Depends(require_permission("inventory.goods_receipts.create")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _receipt_service(db, current_user)
    receipt = await service.create_goods_receipt(data)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="inventory", entity="GoodsReceipt", entity_id=receipt.id,
        user_id=current_user.id, after={"receipt_number": receipt.receipt_number}, context=audit_context,
    )
    return receipt


@router.get("/{receipt_id}", response_model=GoodsReceiptDetail)
async def get_goods_receipt(receipt_id: str, current_user=Depends(require_permission("inventory.goods_receipts.view")), db: AsyncSession = Depends(get_db)):
    service = _receipt_service(db, current_user)
    receipt = await service.get_receipt(receipt_id)
    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goods receipt not found.")
    items = await service.get_items(receipt_id)
    detail = GoodsReceiptDetail.model_validate(receipt)
    detail.items = [GoodsReceiptLineItem.model_validate(item) for item in items]
    return detail


@router.post("/{receipt_id}/complete", response_model=GoodsReceiptRead)
async def complete_goods_receipt(
    receipt_id: str,
    current_user=Depends(require_permission("inventory.goods_receipts.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _receipt_service(db, current_user)
    receipt = await service.complete_receipt(receipt_id, user_id=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="GoodsReceipt", entity_id=receipt.id,
        user_id=current_user.id, after={"status": "completed"}, context=audit_context,
    )
    return receipt


@router.post("/{receipt_id}/cancel", response_model=GoodsReceiptRead)
async def cancel_goods_receipt(
    receipt_id: str,
    current_user=Depends(require_permission("inventory.goods_receipts.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _receipt_service(db, current_user)
    receipt = await service.cancel_receipt(receipt_id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="GoodsReceipt", entity_id=receipt.id,
        user_id=current_user.id, after={"status": "cancelled"}, context=audit_context,
    )
    return receipt


@router.get("/{receipt_id}/items", response_model=list[GoodsReceiptLineItem])
async def list_goods_receipt_items(receipt_id: str, current_user=Depends(require_permission("inventory.goods_receipts.view")), db: AsyncSession = Depends(get_db)):
    service = _receipt_service(db, current_user)
    return await service.get_items(receipt_id)


@router.post("/{receipt_id}/items", response_model=GoodsReceiptLineItem, status_code=status.HTTP_201_CREATED)
async def add_goods_receipt_item(
    receipt_id: str,
    data: GoodsReceiptItemInput,
    current_user=Depends(require_permission("inventory.goods_receipts.create")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _receipt_service(db, current_user)
    item = await service.add_item(receipt_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="GoodsReceipt", entity_id=receipt_id,
        user_id=current_user.id, after={"added_item": item.id}, context=audit_context,
    )
    return item


@router.delete("/{receipt_id}/items/{item_id}")
async def remove_goods_receipt_item(
    receipt_id: str,
    item_id: str,
    current_user=Depends(require_permission("inventory.goods_receipts.create")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _receipt_service(db, current_user)
    await service.remove_item(receipt_id, item_id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="GoodsReceipt", entity_id=receipt_id,
        user_id=current_user.id, after={"removed_item": item_id}, context=audit_context,
    )
    return {"detail": "Goods receipt item removed."}
