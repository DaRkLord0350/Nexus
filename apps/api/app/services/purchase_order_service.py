from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.purchase_order import PurchaseOrder, PurchaseOrderStatus
from app.models.purchase_order_item import PurchaseOrderItem
from app.repositories.purchase_order_repository import PurchaseOrderItemRepository, PurchaseOrderRepository


class PurchaseOrderService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = PurchaseOrderRepository(session, organization_id, is_superuser)
        self.item_repo = PurchaseOrderItemRepository(session, organization_id, is_superuser)

    async def _ensure_unique_number(self, po_number: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_number(po_number)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A purchase order with that number already exists.")

    async def _recompute_totals(self, purchase_order: PurchaseOrder) -> PurchaseOrder:
        items = await self.item_repo.list_for_order(purchase_order.id)
        subtotal = sum(item.unit_cost * item.quantity_ordered for item in items)
        purchase_order.subtotal = subtotal
        purchase_order.total = subtotal + purchase_order.tax_amount + purchase_order.shipping_amount
        return purchase_order

    async def create_purchase_order(self, data, created_by: str | None = None) -> PurchaseOrder:
        po_number = data.po_number or f"PO-{uuid4().hex[:8].upper()}"
        await self._ensure_unique_number(po_number)

        purchase_order = PurchaseOrder(
            po_number=po_number,
            supplier_name=data.supplier_name,
            supplier_email=data.supplier_email,
            supplier_phone=data.supplier_phone,
            warehouse_id=data.warehouse_id,
            currency=data.currency,
            tax_amount=data.tax_amount,
            shipping_amount=data.shipping_amount,
            expected_date=data.expected_date,
            notes=data.notes,
            created_by=created_by,
        )
        purchase_order = await self.repo.create(purchase_order)

        for item_data in data.items:
            item = PurchaseOrderItem(
                purchase_order_id=purchase_order.id,
                product_id=item_data.product_id,
                variant_id=item_data.variant_id,
                quantity_ordered=item_data.quantity_ordered,
                unit_cost=item_data.unit_cost,
                tax_rate=item_data.tax_rate,
                notes=item_data.notes,
            )
            await self.item_repo.create(item)

        purchase_order = await self._recompute_totals(purchase_order)
        return await self.repo.save(purchase_order)

    async def _get_editable_or_404(self, po_id: str) -> PurchaseOrder:
        purchase_order = await self.repo.get_by_id(po_id)
        if not purchase_order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found.")
        return purchase_order

    async def update_purchase_order(self, po_id: str, data) -> PurchaseOrder:
        purchase_order = await self._get_editable_or_404(po_id)
        if purchase_order.status in (PurchaseOrderStatus.received, PurchaseOrderStatus.cancelled):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot edit a received or cancelled purchase order.")

        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(purchase_order, field, value)

        purchase_order = await self._recompute_totals(purchase_order)
        return await self.repo.save(purchase_order)

    async def delete_purchase_order(self, po_id: str) -> None:
        purchase_order = await self._get_editable_or_404(po_id)
        if purchase_order.status != PurchaseOrderStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft purchase orders can be deleted.")
        await self.repo.soft_delete(po_id)

    async def send_purchase_order(self, po_id: str) -> PurchaseOrder:
        purchase_order = await self._get_editable_or_404(po_id)
        if purchase_order.status != PurchaseOrderStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft purchase orders can be sent.")
        items = await self.item_repo.list_for_order(po_id)
        if not items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot send a purchase order with no items.")

        purchase_order.status = PurchaseOrderStatus.sent
        purchase_order.sent_at = datetime.utcnow()
        return await self.repo.save(purchase_order)

    async def cancel_purchase_order(self, po_id: str) -> PurchaseOrder:
        purchase_order = await self._get_editable_or_404(po_id)
        if purchase_order.status in (PurchaseOrderStatus.received, PurchaseOrderStatus.cancelled):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel a received or already-cancelled purchase order.")

        purchase_order.status = PurchaseOrderStatus.cancelled
        purchase_order.cancelled_at = datetime.utcnow()
        return await self.repo.save(purchase_order)

    async def get_purchase_order(self, po_id: str) -> PurchaseOrder | None:
        return await self.repo.get_by_id(po_id)

    async def get_items(self, po_id: str) -> list[PurchaseOrderItem]:
        return await self.item_repo.list_for_order(po_id)

    async def add_item(self, po_id: str, data) -> PurchaseOrderItem:
        purchase_order = await self._get_editable_or_404(po_id)
        if purchase_order.status != PurchaseOrderStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Items can only be added while the purchase order is a draft.")

        item = PurchaseOrderItem(
            purchase_order_id=po_id,
            product_id=data.product_id,
            variant_id=data.variant_id,
            quantity_ordered=data.quantity_ordered,
            unit_cost=data.unit_cost,
            tax_rate=data.tax_rate,
            notes=data.notes,
        )
        item = await self.item_repo.create(item)
        purchase_order = await self._recompute_totals(purchase_order)
        await self.repo.save(purchase_order)
        return item

    async def remove_item(self, po_id: str, item_id: str) -> None:
        purchase_order = await self._get_editable_or_404(po_id)
        if purchase_order.status != PurchaseOrderStatus.draft:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Items can only be removed while the purchase order is a draft.")

        item = await self.item_repo.get_by_id(item_id)
        if not item or item.purchase_order_id != po_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order item not found.")
        await self.item_repo.delete(item_id)

        purchase_order = await self._recompute_totals(purchase_order)
        await self.repo.save(purchase_order)

    async def list_purchase_orders(
        self,
        warehouse_id: str | None = None,
        status_filter: PurchaseOrderStatus | None = None,
        q: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[PurchaseOrder], int]:
        items = await self.repo.list(warehouse_id, status_filter, q, sort_by, sort_order, limit, offset)
        total = await self.repo.count(warehouse_id, status_filter, q)
        return items, total
