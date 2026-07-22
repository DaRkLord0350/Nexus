from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goods_receipt import GoodsReceipt, GoodsReceiptStatus
from app.models.goods_receipt_item import GoodsReceiptItem
from app.models.inventory_transaction import InventoryTransactionType
from app.models.purchase_order import PurchaseOrderStatus
from app.repositories.goods_receipt_repository import GoodsReceiptItemRepository, GoodsReceiptRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.purchase_order_repository import PurchaseOrderItemRepository, PurchaseOrderRepository
from app.services.batch_service import BatchService
from app.services.stock_movement_service import StockMovementService


class GoodsReceiptService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = GoodsReceiptRepository(session, organization_id, is_superuser)
        self.item_repo = GoodsReceiptItemRepository(session, organization_id, is_superuser)
        self.inventory_repo = InventoryRepository(session, organization_id, is_superuser)
        self.po_repo = PurchaseOrderRepository(session, organization_id, is_superuser)
        self.po_item_repo = PurchaseOrderItemRepository(session, organization_id, is_superuser)
        self.batch_service = BatchService(session, organization_id, is_superuser)
        self.movement_service = StockMovementService(session, organization_id, is_superuser)

    async def _ensure_unique_number(self, receipt_number: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_number(receipt_number)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A goods receipt with that number already exists.")

    async def create_goods_receipt(self, data, receiver_id: str | None = None) -> GoodsReceipt:
        receipt_number = data.receipt_number or f"GR-{uuid4().hex[:8].upper()}"
        await self._ensure_unique_number(receipt_number)

        if data.purchase_order_id:
            purchase_order = await self.po_repo.get_by_id(data.purchase_order_id)
            if not purchase_order:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Purchase order not found.")

        receipt = GoodsReceipt(
            receipt_number=receipt_number,
            purchase_order_id=data.purchase_order_id,
            warehouse_id=data.warehouse_id,
            received_date=data.received_date or datetime.utcnow(),
            notes=data.notes,
        )
        receipt = await self.repo.create(receipt)

        for item_data in data.items:
            await self._add_item_row(receipt, item_data)

        return receipt

    async def _add_item_row(self, receipt: GoodsReceipt, item_data) -> GoodsReceiptItem:
        if item_data.purchase_order_item_id:
            po_item = await self.po_item_repo.get_by_id(item_data.purchase_order_item_id)
            if not po_item or po_item.purchase_order_id != receipt.purchase_order_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Purchase order item does not belong to this receipt's purchase order.")

        item = GoodsReceiptItem(
            goods_receipt_id=receipt.id,
            purchase_order_item_id=item_data.purchase_order_item_id,
            product_id=item_data.product_id,
            variant_id=item_data.variant_id,
            quantity_received=item_data.quantity_received,
            unit_cost=item_data.unit_cost,
            batch_number=item_data.batch_number,
            expiry_date=item_data.expiry_date,
            manufactured_date=item_data.manufactured_date,
            bin_id=item_data.bin_id,
            notes=item_data.notes,
        )
        return await self.item_repo.create(item)

    async def _get_draft_or_404(self, receipt_id: str) -> GoodsReceipt:
        receipt = await self.repo.get_by_id(receipt_id)
        if not receipt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goods receipt not found.")
        return receipt

    async def add_item(self, receipt_id: str, item_data) -> GoodsReceiptItem:
        receipt = await self._get_draft_or_404(receipt_id)
        if receipt.status != GoodsReceiptStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Items can only be added while the receipt is a draft.")
        return await self._add_item_row(receipt, item_data)

    async def remove_item(self, receipt_id: str, item_id: str) -> None:
        receipt = await self._get_draft_or_404(receipt_id)
        if receipt.status != GoodsReceiptStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Items can only be removed while the receipt is a draft.")
        item = await self.item_repo.get_by_id(item_id)
        if not item or item.goods_receipt_id != receipt_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goods receipt item not found.")
        await self.item_repo.delete(item_id)

    async def cancel_receipt(self, receipt_id: str) -> GoodsReceipt:
        receipt = await self._get_draft_or_404(receipt_id)
        if receipt.status != GoodsReceiptStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft receipts can be cancelled.")
        receipt.status = GoodsReceiptStatus.cancelled
        return await self.repo.save(receipt)

    async def complete_receipt(self, receipt_id: str, user_id: str | None) -> GoodsReceipt:
        """The Phase 3 orchestration entry point: for every line item this
        creates/updates the Inventory row, creates or tops up a Batch when a
        batch_number is given, and records an InventoryTransaction — all via
        StockMovementService so this is the only place besides direct
        adjustments/transfers that ever changes Inventory.quantity_available.
        Each item's stock movement commits independently (StockMovementService
        owns that transaction boundary); if this loop fails partway through,
        already-processed items remain applied and the receipt stays in
        draft — re-running complete_receipt is not currently idempotent for
        partially-processed receipts, a known limitation worth revisiting if
        goods receipts start failing mid-loop in practice.
        """
        receipt = await self._get_draft_or_404(receipt_id)
        if receipt.status != GoodsReceiptStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft receipts can be completed.")

        items = await self.item_repo.list_for_receipt(receipt_id)
        if not items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot complete a receipt with no items.")

        touched_po_ids: set[str] = set()

        for item in items:
            inventory = await self.inventory_repo.get_or_create_for_update(item.product_id, item.variant_id, receipt.warehouse_id, item.bin_id)
            await self.session.commit()

            batch_id = None
            if item.batch_number:
                batch = await self.batch_service.get_or_create_batch(
                    inventory_id=inventory.id,
                    product_id=item.product_id,
                    variant_id=item.variant_id,
                    warehouse_id=receipt.warehouse_id,
                    batch_number=item.batch_number,
                    quantity=item.quantity_received,
                    expiry_date=item.expiry_date,
                    manufactured_date=item.manufactured_date,
                    cost_price=item.unit_cost,
                )
                await self.session.commit()
                batch_id = batch.id

            await self.movement_service.apply_movement(
                product_id=item.product_id,
                variant_id=item.variant_id,
                warehouse_id=receipt.warehouse_id,
                bin_id=item.bin_id,
                transaction_type=InventoryTransactionType.receive,
                quantity_delta=item.quantity_received,
                reference_type="goods_receipt",
                reference_id=receipt.id,
                batch_id=batch_id,
                user_id=user_id,
                notes=item.notes,
            )

            if item.purchase_order_item_id:
                po_item = await self.po_item_repo.get_by_id(item.purchase_order_item_id)
                if po_item:
                    po_item.quantity_received += item.quantity_received
                    await self.po_item_repo.save(po_item)
                    touched_po_ids.add(po_item.purchase_order_id)

        for po_id in touched_po_ids:
            await self._recompute_po_status(po_id)

        receipt.status = GoodsReceiptStatus.completed
        receipt.receiver_id = user_id
        return await self.repo.save(receipt)

    async def _recompute_po_status(self, po_id: str) -> None:
        purchase_order = await self.po_repo.get_by_id(po_id)
        if not purchase_order:
            return
        items = await self.po_item_repo.list_for_order(po_id)
        if not items:
            return
        if all(item.quantity_received >= item.quantity_ordered for item in items):
            purchase_order.status = PurchaseOrderStatus.received
            purchase_order.received_at = datetime.utcnow()
        elif any(item.quantity_received > 0 for item in items):
            purchase_order.status = PurchaseOrderStatus.partially_received
        await self.po_repo.save(purchase_order)

    async def get_receipt(self, receipt_id: str) -> GoodsReceipt | None:
        return await self.repo.get_by_id(receipt_id)

    async def get_items(self, receipt_id: str) -> list[GoodsReceiptItem]:
        return await self.item_repo.list_for_receipt(receipt_id)

    async def list_receipts(
        self,
        warehouse_id: str | None = None,
        purchase_order_id: str | None = None,
        status_filter: GoodsReceiptStatus | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[GoodsReceipt], int]:
        items = await self.repo.list(warehouse_id, purchase_order_id, status_filter, q, limit, offset)
        total = await self.repo.count(warehouse_id, purchase_order_id, status_filter, q)
        return items, total
