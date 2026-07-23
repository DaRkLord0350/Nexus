from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory_transaction import InventoryTransactionType
from app.models.order import Order, OrderPriority, OrderStatus, PaymentStatus
from app.models.order_item import OrderItem
from app.models.order_note import OrderNote
from app.models.order_status_history import OrderStatusHistory
from app.repositories.order_repository import (
    OrderItemRepository,
    OrderNoteRepository,
    OrderRepository,
    OrderStatusHistoryRepository,
)
from app.repositories.product_repository import ProductRepository
from app.repositories.variant_repository import VariantRepository
from app.services.coupon_service import CouponService
from app.services.pricing_service import PricingService
from app.services.stock_movement_service import StockMovementService

# States from which cancellation is still possible (before the order has
# physically left a warehouse). Once shipped, only a Return can unwind it.
CANCELLABLE_STATES = {
    OrderStatus.draft, OrderStatus.pending, OrderStatus.confirmed, OrderStatus.processing,
    OrderStatus.packed, OrderStatus.ready_to_ship, OrderStatus.partially_fulfilled, OrderStatus.backordered,
}

ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.draft: {OrderStatus.pending, OrderStatus.cancelled},
    OrderStatus.pending: {OrderStatus.confirmed, OrderStatus.cancelled, OrderStatus.hold},
    OrderStatus.confirmed: {OrderStatus.processing, OrderStatus.cancelled, OrderStatus.hold},
    OrderStatus.processing: {OrderStatus.packed, OrderStatus.partially_fulfilled, OrderStatus.backordered, OrderStatus.cancelled, OrderStatus.hold},
    OrderStatus.packed: {OrderStatus.ready_to_ship, OrderStatus.cancelled, OrderStatus.hold},
    OrderStatus.ready_to_ship: {OrderStatus.shipped, OrderStatus.cancelled, OrderStatus.hold},
    OrderStatus.shipped: {OrderStatus.out_for_delivery, OrderStatus.delivered},
    OrderStatus.out_for_delivery: {OrderStatus.delivered, OrderStatus.failed},
    OrderStatus.delivered: set(),
    OrderStatus.cancelled: set(),
    OrderStatus.failed: {OrderStatus.pending, OrderStatus.cancelled},
    OrderStatus.hold: set(),
    OrderStatus.partially_fulfilled: {OrderStatus.processing, OrderStatus.packed, OrderStatus.cancelled},
    OrderStatus.backordered: {OrderStatus.processing, OrderStatus.cancelled},
}


class OrderService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = OrderRepository(session, organization_id, is_superuser)
        self.item_repo = OrderItemRepository(session, organization_id, is_superuser)
        self.history_repo = OrderStatusHistoryRepository(session, organization_id, is_superuser)
        self.note_repo = OrderNoteRepository(session, organization_id, is_superuser)
        self.product_repo = ProductRepository(session, organization_id, is_superuser)
        self.variant_repo = VariantRepository(session, organization_id, is_superuser)
        self.pricing_service = PricingService(session, organization_id, is_superuser)
        self.coupon_service = CouponService(session, organization_id, is_superuser)
        self.stock_service = StockMovementService(session, organization_id, is_superuser)

    def _generate_order_number(self) -> str:
        return f"ORD-{uuid4().hex[:10].upper()}"

    async def _check_stock(self, product, variant_id: str | None, warehouse_id: str, quantity: int) -> None:
        if not product.track_inventory or product.allow_backorders:
            return
        inventory = await self.stock_service.inventory_repo.find_one(product.id, variant_id, warehouse_id)
        available = (inventory.quantity_available - inventory.quantity_reserved) if inventory else 0
        if quantity > available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {available} unit(s) of {product.name} available at the selected warehouse.",
            )

    async def _resolve_line_item(self, data, currency: str) -> tuple[OrderItem, object]:
        product = await self.product_repo.get_by_id(data.product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

        variant = None
        if data.variant_id:
            variant = await self.variant_repo.get_by_id(data.variant_id)
            if not variant or variant.product_id != product.id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found for this product.")

        unit_price = data.unit_price
        if unit_price is None:
            price = await self.pricing_service.resolve_price(product.id, currency, data.variant_id)
            if not price:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"No price configured for product {product.name}.")
            unit_price = price.selling_price

        line_total = round(unit_price * data.quantity - data.discount_amount + data.tax_amount, 2)
        item = OrderItem(
            product_id=product.id,
            variant_id=data.variant_id,
            warehouse_id=data.warehouse_id,
            sku=variant.sku if variant else product.sku,
            product_name=product.name,
            quantity=data.quantity,
            unit_price=unit_price,
            discount_amount=data.discount_amount,
            tax_amount=data.tax_amount,
            total=line_total,
            gift_note=data.gift_note,
        )
        return item, product

    async def create_order(self, data, created_by: str | None = None) -> Order:
        order_number = self._generate_order_number()
        while await self.repo.get_by_number(order_number):
            order_number = self._generate_order_number()

        resolved_items: list[OrderItem] = []
        stock_deductions: list[OrderItem] = []
        for item_data in data.items:
            item, product = await self._resolve_line_item(item_data, data.currency)
            resolved_items.append(item)
            if item.warehouse_id:
                await self._check_stock(product, item.variant_id, item.warehouse_id, item.quantity)
                if product.track_inventory:
                    stock_deductions.append(item)

        subtotal = sum(item.unit_price * item.quantity for item in resolved_items)
        line_discount_total = sum(item.discount_amount for item in resolved_items)
        tax_total = sum(item.tax_amount for item in resolved_items)

        coupon_id = None
        coupon_discount = 0.0
        coupon_code = data.coupon_code.strip().upper() if data.coupon_code else None
        if coupon_code:
            result = await self.coupon_service.validate_coupon(
                code=coupon_code, order_amount=subtotal, product_ids=[item.product_id for item in resolved_items], customer_id=data.customer_id,
            )
            if not result["valid"]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["reason"] or "Coupon is not valid.")
            coupon_id = result["coupon_id"]
            coupon_discount = result["discount_amount"]

        discount_total = round(line_discount_total + coupon_discount, 2)
        total = round(subtotal - discount_total + tax_total + data.shipping_amount, 2)

        initial_status = OrderStatus.pending if resolved_items else OrderStatus.draft

        order = Order(
            order_number=order_number,
            customer_id=data.customer_id,
            cart_id=data.cart_id,
            status=initial_status,
            currency=data.currency,
            subtotal=round(subtotal, 2),
            discount_amount=discount_total,
            tax_amount=round(tax_total, 2),
            shipping_amount=data.shipping_amount,
            total=total,
            coupon_id=coupon_id,
            coupon_code=coupon_code,
            payment_method=data.payment_method,
            shipping_method=data.shipping_method,
            billing_address_id=None,
            billing_first_name=data.billing_address.first_name,
            billing_last_name=data.billing_address.last_name,
            billing_company=data.billing_address.company,
            billing_phone=data.billing_address.phone,
            billing_line1=data.billing_address.line1,
            billing_line2=data.billing_address.line2,
            billing_city=data.billing_address.city,
            billing_state=data.billing_address.state,
            billing_postal_code=data.billing_address.postal_code,
            billing_country=data.billing_address.country.upper(),
            shipping_address_id=None,
            shipping_first_name=data.shipping_address.first_name,
            shipping_last_name=data.shipping_address.last_name,
            shipping_company=data.shipping_address.company,
            shipping_phone=data.shipping_address.phone,
            shipping_line1=data.shipping_address.line1,
            shipping_line2=data.shipping_address.line2,
            shipping_city=data.shipping_address.city,
            shipping_state=data.shipping_address.state,
            shipping_postal_code=data.shipping_address.postal_code,
            shipping_country=data.shipping_address.country.upper(),
            customer_note=data.customer_note,
            gift_note=data.gift_note,
            priority=OrderPriority(data.priority.value if hasattr(data.priority, "value") else data.priority),
            source=data.source,
            tags=data.tags,
            placed_at=datetime.utcnow() if resolved_items else None,
            created_by=created_by,
        )
        self.repo._add_tenant_on_create(order)
        order = await self.repo.save_no_commit(order)

        for item in resolved_items:
            item.order_id = order.id
            await self.item_repo.create_no_commit(item)

        history = OrderStatusHistory(order_id=order.id, from_status=None, to_status=initial_status.value, changed_by=created_by)
        await self.history_repo.create_no_commit(history)

        await self.session.commit()
        await self.session.refresh(order)

        if coupon_id:
            await self.coupon_service.repo.increment_used_count(coupon_id)

        for item in stock_deductions:
            await self.stock_service.apply_movement(
                product_id=item.product_id, variant_id=item.variant_id, warehouse_id=item.warehouse_id,
                transaction_type=InventoryTransactionType.sale, quantity_delta=-item.quantity,
                field="quantity_available", reference_type="order", reference_id=order.id, user_id=created_by,
            )

        return order

    async def _get_or_404(self, order_id: str) -> Order:
        order = await self.repo.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
        return order

    async def get_order(self, order_id: str) -> Order | None:
        return await self.repo.get_by_id(order_id)

    async def get_items(self, order_id: str) -> list[OrderItem]:
        return await self.item_repo.list_for_order(order_id)

    async def get_status_history(self, order_id: str) -> list[OrderStatusHistory]:
        return await self.history_repo.list_for_order(order_id)

    async def get_notes(self, order_id: str) -> list[OrderNote]:
        return await self.note_repo.list_for_order(order_id)

    async def add_note(self, order_id: str, data, created_by: str | None = None) -> OrderNote:
        await self._get_or_404(order_id)
        note = OrderNote(order_id=order_id, note=data.note, is_customer_visible=data.is_customer_visible, created_by=created_by)
        return await self.note_repo.create(note)

    async def update_order(self, order_id: str, data) -> Order:
        order = await self._get_or_404(order_id)
        changes = data.model_dump(exclude_unset=True)
        if "priority" in changes and changes["priority"] is not None:
            changes["priority"] = OrderPriority(changes["priority"].value if hasattr(changes["priority"], "value") else changes["priority"])
        for field, value in changes.items():
            setattr(order, field, value)
        return await self.repo.save(order)

    async def list_orders(
        self,
        customer_id: str | None = None,
        status_filter: OrderStatus | None = None,
        priority: OrderPriority | None = None,
        requires_manual_review: bool | None = None,
        q: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Order], int]:
        items = await self.repo.list(customer_id, status_filter, priority, requires_manual_review, q, sort_by, sort_order, limit, offset)
        total = await self.repo.count(customer_id, status_filter, priority, requires_manual_review, q)
        return items, total

    async def bulk_update_priority(self, order_ids: list[str], priority: OrderPriority) -> int:
        return await self.repo.bulk_update_priority(order_ids, priority)

    async def bulk_update_tags(self, order_ids: list[str], tags: str) -> int:
        return await self.repo.bulk_update_tags(order_ids, tags)

    # ------------------------------------------------------------------
    # Status workflow
    # ------------------------------------------------------------------
    async def _transition(self, order_id: str, new_status: OrderStatus, changed_by: str | None = None, notes: str | None = None) -> Order:
        order = await self._get_or_404(order_id)
        allowed = ALLOWED_TRANSITIONS.get(order.status, set())
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot move an order from '{order.status.value}' to '{new_status.value}'.",
            )

        from_status = order.status
        order.status = new_status

        timestamp_field = {
            OrderStatus.confirmed: "confirmed_at",
            OrderStatus.packed: "packed_at",
            OrderStatus.shipped: "shipped_at",
            OrderStatus.delivered: "delivered_at",
            OrderStatus.cancelled: "cancelled_at",
        }.get(new_status)
        if timestamp_field:
            setattr(order, timestamp_field, datetime.utcnow())
        if new_status == OrderStatus.pending and from_status == OrderStatus.draft:
            order.placed_at = datetime.utcnow()
        if new_status == OrderStatus.delivered:
            order.payment_status = PaymentStatus.paid if order.payment_method == "cod" else order.payment_status

        order = await self.repo.save_no_commit(order)
        history = OrderStatusHistory(order_id=order.id, from_status=from_status.value, to_status=new_status.value, notes=notes, changed_by=changed_by)
        await self.history_repo.create_no_commit(history)
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def place_order(self, order_id: str, changed_by: str | None = None) -> Order:
        return await self._transition(order_id, OrderStatus.pending, changed_by)

    async def confirm_order(self, order_id: str, changed_by: str | None = None) -> Order:
        return await self._transition(order_id, OrderStatus.confirmed, changed_by)

    async def start_processing(self, order_id: str, changed_by: str | None = None) -> Order:
        return await self._transition(order_id, OrderStatus.processing, changed_by)

    async def pack_order(self, order_id: str, changed_by: str | None = None) -> Order:
        return await self._transition(order_id, OrderStatus.packed, changed_by)

    async def mark_ready_to_ship(self, order_id: str, changed_by: str | None = None) -> Order:
        return await self._transition(order_id, OrderStatus.ready_to_ship, changed_by)

    async def ship_order(self, order_id: str, changed_by: str | None = None) -> Order:
        return await self._transition(order_id, OrderStatus.shipped, changed_by)

    async def mark_out_for_delivery(self, order_id: str, changed_by: str | None = None) -> Order:
        return await self._transition(order_id, OrderStatus.out_for_delivery, changed_by)

    async def deliver_order(self, order_id: str, changed_by: str | None = None) -> Order:
        return await self._transition(order_id, OrderStatus.delivered, changed_by)

    async def mark_partially_fulfilled(self, order_id: str, changed_by: str | None = None) -> Order:
        return await self._transition(order_id, OrderStatus.partially_fulfilled, changed_by)

    async def mark_backordered(self, order_id: str, changed_by: str | None = None) -> Order:
        return await self._transition(order_id, OrderStatus.backordered, changed_by)

    async def mark_failed(self, order_id: str, changed_by: str | None = None, reason: str | None = None) -> Order:
        return await self._transition(order_id, OrderStatus.failed, changed_by, notes=reason)

    async def hold_order(self, order_id: str, changed_by: str | None = None, reason: str | None = None) -> Order:
        order = await self._get_or_404(order_id)
        if order.status == OrderStatus.hold:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order is already on hold.")
        if order.status in (OrderStatus.delivered, OrderStatus.cancelled):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot hold a delivered or cancelled order.")

        previous = order.status
        order.previous_status = previous
        order.status = OrderStatus.hold
        order = await self.repo.save_no_commit(order)
        history = OrderStatusHistory(order_id=order.id, from_status=previous.value, to_status=OrderStatus.hold.value, notes=reason, changed_by=changed_by)
        await self.history_repo.create_no_commit(history)
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def resume_order(self, order_id: str, changed_by: str | None = None) -> Order:
        order = await self._get_or_404(order_id)
        if order.status != OrderStatus.hold or not order.previous_status:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order is not currently on hold.")

        resumed_status = order.previous_status
        order.status = resumed_status
        order.previous_status = None
        order = await self.repo.save_no_commit(order)
        history = OrderStatusHistory(order_id=order.id, from_status=OrderStatus.hold.value, to_status=resumed_status.value, changed_by=changed_by)
        await self.history_repo.create_no_commit(history)
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def cancel_order(self, order_id: str, changed_by: str | None = None, reason: str | None = None) -> Order:
        order = await self._get_or_404(order_id)
        cancellable_from = order.previous_status if order.status == OrderStatus.hold else order.status
        if cancellable_from not in CANCELLABLE_STATES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot cancel an order in '{order.status.value}' status.")

        items = await self.item_repo.list_for_order(order_id)
        for item in items:
            if item.warehouse_id:
                restock_qty = item.quantity - item.quantity_returned
                if restock_qty > 0:
                    await self.stock_service.apply_movement(
                        product_id=item.product_id, variant_id=item.variant_id, warehouse_id=item.warehouse_id,
                        transaction_type=InventoryTransactionType.return_, quantity_delta=restock_qty,
                        field="quantity_available", reference_type="order_cancel", reference_id=order.id, user_id=changed_by,
                    )

        from_status = order.status
        order.status = OrderStatus.cancelled
        order.cancelled_at = datetime.utcnow()
        order.cancelled_reason = reason
        order = await self.repo.save_no_commit(order)
        history = OrderStatusHistory(order_id=order.id, from_status=from_status.value, to_status=OrderStatus.cancelled.value, notes=reason, changed_by=changed_by)
        await self.history_repo.create_no_commit(history)
        await self.session.commit()
        await self.session.refresh(order)
        return order
