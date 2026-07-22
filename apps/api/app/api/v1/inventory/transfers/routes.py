from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.models.stock_transfer import StockTransferStatus as ModelStockTransferStatus
from app.schemas.stock_transfer import (
    StockTransferCreateRequest,
    StockTransferDetail,
    StockTransferLineItem,
    StockTransferLineItemInput,
    StockTransferListResponse,
    StockTransferRead,
)
from app.services.audit_service import AuditService
from app.services.transfer_service import TransferService

router = APIRouter(prefix="/transfers", tags=["inventory-transfers"])


def _transfer_service(db: AsyncSession, current_user) -> TransferService:
    return TransferService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=StockTransferListResponse)
async def list_transfers(
    from_warehouse_id: str | None = Query(None),
    to_warehouse_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    q: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("inventory.transfers.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _transfer_service(db, current_user)
    model_status = ModelStockTransferStatus(status_filter) if status_filter else None
    items, total = await service.list_transfers(from_warehouse_id, to_warehouse_id, model_status, q, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=StockTransferRead, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    data: StockTransferCreateRequest,
    current_user=Depends(require_permission("inventory.transfers.create")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _transfer_service(db, current_user)
    transfer = await service.create_transfer(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="inventory", entity="StockTransfer", entity_id=transfer.id,
        user_id=current_user.id, after={"transfer_number": transfer.transfer_number}, context=audit_context,
    )
    return transfer


@router.get("/{transfer_id}", response_model=StockTransferDetail)
async def get_transfer(transfer_id: str, current_user=Depends(require_permission("inventory.transfers.view")), db: AsyncSession = Depends(get_db)):
    service = _transfer_service(db, current_user)
    transfer = await service.get_transfer(transfer_id)
    if not transfer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock transfer not found.")
    items = await service.get_items(transfer_id)
    detail = StockTransferDetail.model_validate(transfer)
    detail.items = [StockTransferLineItem.model_validate(item) for item in items]
    return detail


@router.post("/{transfer_id}/pack", response_model=StockTransferRead)
async def pack_transfer(
    transfer_id: str,
    current_user=Depends(require_permission("inventory.transfers.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _transfer_service(db, current_user)
    transfer = await service.pack_transfer(transfer_id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="StockTransfer", entity_id=transfer.id,
        user_id=current_user.id, after={"status": "packed"}, context=audit_context,
    )
    return transfer


@router.post("/{transfer_id}/ship", response_model=StockTransferRead)
async def ship_transfer(
    transfer_id: str,
    current_user=Depends(require_permission("inventory.transfers.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _transfer_service(db, current_user)
    transfer = await service.ship_transfer(transfer_id, user_id=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="StockTransfer", entity_id=transfer.id,
        user_id=current_user.id, after={"status": "shipped"}, context=audit_context,
    )
    return transfer


@router.post("/{transfer_id}/receive", response_model=StockTransferRead)
async def receive_transfer(
    transfer_id: str,
    current_user=Depends(require_permission("inventory.transfers.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _transfer_service(db, current_user)
    transfer = await service.receive_transfer(transfer_id, user_id=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="StockTransfer", entity_id=transfer.id,
        user_id=current_user.id, after={"status": "received"}, context=audit_context,
    )
    return transfer


@router.post("/{transfer_id}/cancel", response_model=StockTransferRead)
async def cancel_transfer(
    transfer_id: str,
    current_user=Depends(require_permission("inventory.transfers.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _transfer_service(db, current_user)
    transfer = await service.cancel_transfer(transfer_id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="StockTransfer", entity_id=transfer.id,
        user_id=current_user.id, after={"status": "cancelled"}, context=audit_context,
    )
    return transfer


@router.get("/{transfer_id}/items", response_model=list[StockTransferLineItem])
async def list_transfer_items(transfer_id: str, current_user=Depends(require_permission("inventory.transfers.view")), db: AsyncSession = Depends(get_db)):
    service = _transfer_service(db, current_user)
    return await service.get_items(transfer_id)


@router.post("/{transfer_id}/items", response_model=StockTransferLineItem, status_code=status.HTTP_201_CREATED)
async def add_transfer_item(
    transfer_id: str,
    data: StockTransferLineItemInput,
    current_user=Depends(require_permission("inventory.transfers.create")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _transfer_service(db, current_user)
    item = await service.add_item(transfer_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="StockTransfer", entity_id=transfer_id,
        user_id=current_user.id, after={"added_item": item.id}, context=audit_context,
    )
    return item


@router.delete("/{transfer_id}/items/{item_id}")
async def remove_transfer_item(
    transfer_id: str,
    item_id: str,
    current_user=Depends(require_permission("inventory.transfers.create")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _transfer_service(db, current_user)
    await service.remove_item(transfer_id, item_id)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="StockTransfer", entity_id=transfer_id,
        user_id=current_user.id, after={"removed_item": item_id}, context=audit_context,
    )
    return {"detail": "Stock transfer item removed."}
