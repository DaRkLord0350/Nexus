from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory_transaction import InventoryTransactionType
from app.models.stock_transfer import StockTransfer, StockTransferStatus
from app.models.stock_transfer_item import StockTransferItem
from app.repositories.stock_transfer_repository import StockTransferItemRepository, StockTransferRepository
from app.services.stock_movement_service import StockMovementService


class TransferService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = StockTransferRepository(session, organization_id, is_superuser)
        self.item_repo = StockTransferItemRepository(session, organization_id, is_superuser)
        self.movement_service = StockMovementService(session, organization_id, is_superuser)

    async def _ensure_unique_number(self, transfer_number: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_number(transfer_number)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A stock transfer with that number already exists.")

    async def create_transfer(self, data, created_by: str | None = None) -> StockTransfer:
        if data.from_warehouse_id == data.to_warehouse_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source and destination warehouse must be different.")

        transfer_number = data.transfer_number or f"TR-{uuid4().hex[:8].upper()}"
        await self._ensure_unique_number(transfer_number)

        transfer = StockTransfer(
            transfer_number=transfer_number,
            from_warehouse_id=data.from_warehouse_id,
            to_warehouse_id=data.to_warehouse_id,
            notes=data.notes,
            created_by=created_by,
        )
        transfer = await self.repo.create(transfer)

        for item_data in data.items:
            item = StockTransferItem(
                stock_transfer_id=transfer.id,
                product_id=item_data.product_id,
                variant_id=item_data.variant_id,
                quantity_requested=item_data.quantity_requested,
                notes=item_data.notes,
            )
            await self.item_repo.create(item)

        return transfer

    async def _get_or_404(self, transfer_id: str) -> StockTransfer:
        transfer = await self.repo.get_by_id(transfer_id)
        if not transfer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock transfer not found.")
        return transfer

    async def add_item(self, transfer_id: str, item_data) -> StockTransferItem:
        transfer = await self._get_or_404(transfer_id)
        if transfer.status != StockTransferStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Items can only be added while the transfer is a draft.")
        item = StockTransferItem(
            stock_transfer_id=transfer_id,
            product_id=item_data.product_id,
            variant_id=item_data.variant_id,
            quantity_requested=item_data.quantity_requested,
            notes=item_data.notes,
        )
        return await self.item_repo.create(item)

    async def remove_item(self, transfer_id: str, item_id: str) -> None:
        transfer = await self._get_or_404(transfer_id)
        if transfer.status != StockTransferStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Items can only be removed while the transfer is a draft.")
        item = await self.item_repo.get_by_id(item_id)
        if not item or item.stock_transfer_id != transfer_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock transfer item not found.")
        await self.item_repo.delete(item_id)

    async def pack_transfer(self, transfer_id: str) -> StockTransfer:
        transfer = await self._get_or_404(transfer_id)
        if transfer.status != StockTransferStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft transfers can be packed.")
        items = await self.item_repo.list_for_transfer(transfer_id)
        if not items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot pack a transfer with no items.")
        transfer.status = StockTransferStatus.packed
        return await self.repo.save(transfer)

    async def ship_transfer(self, transfer_id: str, user_id: str | None) -> StockTransfer:
        transfer = await self._get_or_404(transfer_id)
        if transfer.status != StockTransferStatus.packed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only packed transfers can be shipped.")

        items = await self.item_repo.list_for_transfer(transfer_id)
        for item in items:
            await self.movement_service.apply_movement(
                product_id=item.product_id,
                variant_id=item.variant_id,
                warehouse_id=transfer.from_warehouse_id,
                transaction_type=InventoryTransactionType.transfer,
                quantity_delta=-item.quantity_requested,
                reference_type="stock_transfer",
                reference_id=transfer.id,
                batch_id=item.batch_id,
                user_id=user_id,
            )
            item.quantity_shipped = item.quantity_requested
            await self.item_repo.save(item)

        transfer.status = StockTransferStatus.shipped
        transfer.shipped_at = datetime.utcnow()
        return await self.repo.save(transfer)

    async def receive_transfer(self, transfer_id: str, user_id: str | None) -> StockTransfer:
        transfer = await self._get_or_404(transfer_id)
        if transfer.status != StockTransferStatus.shipped:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only shipped transfers can be received.")

        items = await self.item_repo.list_for_transfer(transfer_id)
        for item in items:
            await self.movement_service.apply_movement(
                product_id=item.product_id,
                variant_id=item.variant_id,
                warehouse_id=transfer.to_warehouse_id,
                transaction_type=InventoryTransactionType.transfer,
                quantity_delta=item.quantity_shipped,
                reference_type="stock_transfer",
                reference_id=transfer.id,
                batch_id=item.batch_id,
                user_id=user_id,
            )
            item.quantity_received = item.quantity_shipped
            await self.item_repo.save(item)

        transfer.status = StockTransferStatus.received
        transfer.received_at = datetime.utcnow()
        return await self.repo.save(transfer)

    async def cancel_transfer(self, transfer_id: str) -> StockTransfer:
        transfer = await self._get_or_404(transfer_id)
        if transfer.status not in (StockTransferStatus.draft, StockTransferStatus.packed):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft or packed transfers can be cancelled.")
        transfer.status = StockTransferStatus.cancelled
        transfer.cancelled_at = datetime.utcnow()
        return await self.repo.save(transfer)

    async def get_transfer(self, transfer_id: str) -> StockTransfer | None:
        return await self.repo.get_by_id(transfer_id)

    async def get_items(self, transfer_id: str) -> list[StockTransferItem]:
        return await self.item_repo.list_for_transfer(transfer_id)

    async def list_transfers(
        self,
        from_warehouse_id: str | None = None,
        to_warehouse_id: str | None = None,
        status_filter: StockTransferStatus | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[StockTransfer], int]:
        items = await self.repo.list(from_warehouse_id, to_warehouse_id, status_filter, q, limit, offset)
        total = await self.repo.count(from_warehouse_id, to_warehouse_id, status_filter, q)
        return items, total
