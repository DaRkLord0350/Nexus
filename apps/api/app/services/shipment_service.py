from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import OrderStatus
from app.models.shipment import Shipment, ShipmentStatus
from app.models.shipment_item import ShipmentItem
from app.repositories.order_repository import OrderItemRepository, OrderRepository
from app.repositories.shipment_repository import ShipmentItemRepository, ShipmentRepository
from app.repositories.shipping_provider_repository import ShippingProviderRepository
from app.repositories.warehouse_repository import WarehouseRepository

ALLOWED_TRANSITIONS: dict[ShipmentStatus, set[ShipmentStatus]] = {
    ShipmentStatus.pending: {ShipmentStatus.label_generated, ShipmentStatus.cancelled},
    ShipmentStatus.label_generated: {ShipmentStatus.picked_up, ShipmentStatus.cancelled},
    ShipmentStatus.picked_up: {ShipmentStatus.in_transit, ShipmentStatus.cancelled},
    ShipmentStatus.in_transit: {ShipmentStatus.out_for_delivery, ShipmentStatus.failed_delivery, ShipmentStatus.delivered},
    ShipmentStatus.out_for_delivery: {ShipmentStatus.delivered, ShipmentStatus.failed_delivery},
    ShipmentStatus.failed_delivery: {ShipmentStatus.out_for_delivery, ShipmentStatus.returned_to_origin, ShipmentStatus.cancelled},
    ShipmentStatus.delivered: set(),
    ShipmentStatus.returned_to_origin: set(),
    ShipmentStatus.cancelled: set(),
}


class ShipmentService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = ShipmentRepository(session, organization_id, is_superuser)
        self.item_repo = ShipmentItemRepository(session, organization_id, is_superuser)
        self.order_repo = OrderRepository(session, organization_id, is_superuser)
        self.order_item_repo = OrderItemRepository(session, organization_id, is_superuser)
        self.warehouse_repo = WarehouseRepository(session, organization_id, is_superuser)
        self.provider_repo = ShippingProviderRepository(session, organization_id, is_superuser)

    def _generate_shipment_number(self) -> str:
        return f"SHP-{uuid4().hex[:10].upper()}"

    async def _allocate_warehouse(self, order) -> str:
        """Picks a warehouse for a new shipment. Prefers a warehouse whose
        country/state matches the order's shipping address (a proxy for
        "nearest warehouse" since no geocoding/lat-long exists on Warehouse
        yet), then falls back to the org default, then any active warehouse."""
        warehouses = await self.warehouse_repo.list(is_active=True, limit=200)
        if not warehouses:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active warehouse is configured for fulfillment.")

        for warehouse in warehouses:
            if warehouse.country and order.shipping_country and warehouse.country == order.shipping_country:
                if warehouse.state and order.shipping_state and warehouse.state == order.shipping_state:
                    return warehouse.id
        for warehouse in warehouses:
            if warehouse.country and order.shipping_country and warehouse.country == order.shipping_country:
                return warehouse.id

        default_warehouse = await self.warehouse_repo.get_default()
        if default_warehouse:
            return default_warehouse.id

        return warehouses[0].id

    async def _select_provider_id(self, requested_id: str | None, is_cod: bool) -> str | None:
        if requested_id:
            provider = await self.provider_repo.get_by_id(requested_id)
            if not provider:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipping provider not found.")
            return provider.id

        default_provider = await self.provider_repo.get_default()
        if default_provider and (not is_cod or default_provider.supports_cod):
            return default_provider.id

        candidates = await self.provider_repo.list(is_active=True, limit=200)
        for provider in sorted(candidates, key=lambda p: p.priority):
            if not is_cod or provider.supports_cod:
                return provider.id
        return None

    async def create_shipment(self, data, created_by: str | None = None) -> Shipment:
        order = await self.order_repo.get_by_id(data.order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
        if order.status in (OrderStatus.draft, OrderStatus.cancelled, OrderStatus.delivered):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot create a shipment for an order in '{order.status.value}' status.")

        resolved_items: list[ShipmentItem] = []
        for item_data in data.items:
            order_item = await self.order_item_repo.get_by_id(item_data.order_item_id)
            if not order_item or order_item.order_id != order.id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found on this order.")

            already_shipped = await self.item_repo.sum_shipped_for_order_item(order_item.id)
            remaining = order_item.quantity - already_shipped
            if item_data.quantity > remaining:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Only {remaining} unit(s) of {order_item.product_name} remain unshipped.")

            resolved_items.append(ShipmentItem(
                order_item_id=order_item.id, product_id=order_item.product_id, variant_id=order_item.variant_id,
                quantity=item_data.quantity, sku=order_item.sku, product_name=order_item.product_name,
            ))

        warehouse_id = data.warehouse_id or await self._allocate_warehouse(order)
        provider_id = await self._select_provider_id(data.shipping_provider_id, data.is_cod)

        shipping_cost = data.shipping_cost
        if shipping_cost is None:
            provider = await self.provider_repo.get_by_id(provider_id) if provider_id else None
            shipping_cost = provider.base_rate if provider and provider.base_rate is not None else 0.0

        provider = await self.provider_repo.get_by_id(provider_id) if provider_id else None

        shipment_number = self._generate_shipment_number()
        while await self.repo.get_by_number(shipment_number):
            shipment_number = self._generate_shipment_number()

        shipment = Shipment(
            shipment_number=shipment_number,
            order_id=order.id,
            warehouse_id=warehouse_id,
            shipping_provider_id=provider_id,
            carrier_name=provider.name if provider else None,
            service_type=data.service_type,
            weight=data.weight,
            length=data.length,
            width=data.width,
            height=data.height,
            shipping_cost=shipping_cost,
            insurance_amount=data.insurance_amount,
            is_cod=data.is_cod,
            cod_amount=data.cod_amount,
            notes=data.notes,
            created_by=created_by,
        )
        self.repo._add_tenant_on_create(shipment)
        shipment = await self.repo.save_no_commit(shipment)

        for item in resolved_items:
            item.shipment_id = shipment.id
            await self.item_repo.create_no_commit(item)

        for item_data in data.items:
            order_item = await self.order_item_repo.get_by_id(item_data.order_item_id)
            order_item.quantity_fulfilled = order_item.quantity_fulfilled + item_data.quantity
            await self.order_item_repo.save_no_commit(order_item)

        await self.session.commit()
        await self.session.refresh(shipment)
        return shipment

    async def _get_or_404(self, shipment_id: str) -> Shipment:
        shipment = await self.repo.get_by_id(shipment_id)
        if not shipment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found.")
        return shipment

    async def get_shipment(self, shipment_id: str) -> Shipment | None:
        return await self.repo.get_by_id(shipment_id)

    async def get_items(self, shipment_id: str) -> list[ShipmentItem]:
        return await self.item_repo.list_for_shipment(shipment_id)

    async def update_shipment(self, shipment_id: str, data) -> Shipment:
        shipment = await self._get_or_404(shipment_id)
        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(shipment, field, value)
        return await self.repo.save(shipment)

    async def list_shipments(
        self,
        order_id: str | None = None,
        warehouse_id: str | None = None,
        shipping_provider_id: str | None = None,
        status_filter: ShipmentStatus | None = None,
        q: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Shipment], int]:
        items = await self.repo.list(order_id, warehouse_id, shipping_provider_id, status_filter, q, sort_by, sort_order, limit, offset)
        total = await self.repo.count(order_id, warehouse_id, shipping_provider_id, status_filter, q)
        return items, total

    async def _transition(self, shipment_id: str, new_status: ShipmentStatus) -> Shipment:
        shipment = await self._get_or_404(shipment_id)
        allowed = ALLOWED_TRANSITIONS.get(shipment.status, set())
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot move a shipment from '{shipment.status.value}' to '{new_status.value}'.",
            )
        shipment.status = new_status
        return shipment

    async def generate_label(self, shipment_id: str) -> Shipment:
        shipment = await self._transition(shipment_id, ShipmentStatus.label_generated)
        if not shipment.tracking_number:
            shipment.tracking_number = f"TRK{uuid4().hex[:12].upper()}"
        return await self.repo.save(shipment)

    async def mark_picked_up(self, shipment_id: str) -> Shipment:
        shipment = await self._transition(shipment_id, ShipmentStatus.picked_up)
        shipment.picked_up_at = datetime.utcnow()
        return await self.repo.save(shipment)

    async def mark_in_transit(self, shipment_id: str) -> Shipment:
        shipment = await self._transition(shipment_id, ShipmentStatus.in_transit)
        return await self.repo.save(shipment)

    async def mark_out_for_delivery(self, shipment_id: str) -> Shipment:
        shipment = await self._transition(shipment_id, ShipmentStatus.out_for_delivery)
        return await self.repo.save(shipment)

    async def mark_delivered(self, shipment_id: str) -> Shipment:
        shipment = await self._transition(shipment_id, ShipmentStatus.delivered)
        shipment.delivered_at = datetime.utcnow()
        return await self.repo.save(shipment)

    async def mark_failed_delivery(self, shipment_id: str, reason: str | None = None) -> Shipment:
        shipment = await self._transition(shipment_id, ShipmentStatus.failed_delivery)
        shipment.delivery_attempts = shipment.delivery_attempts + 1
        if reason:
            shipment.notes = f"{shipment.notes}\n{reason}" if shipment.notes else reason
        return await self.repo.save(shipment)

    async def mark_returned(self, shipment_id: str) -> Shipment:
        shipment = await self._transition(shipment_id, ShipmentStatus.returned_to_origin)
        return await self.repo.save(shipment)

    async def cancel_shipment(self, shipment_id: str, reason: str | None = None) -> Shipment:
        shipment = await self._transition(shipment_id, ShipmentStatus.cancelled)
        shipment.cancelled_at = datetime.utcnow()
        if reason:
            shipment.notes = f"{shipment.notes}\n{reason}" if shipment.notes else reason

        items = await self.item_repo.list_for_shipment(shipment_id)
        for item in items:
            order_item = await self.order_item_repo.get_by_id(item.order_item_id)
            if order_item:
                order_item.quantity_fulfilled = max(0, order_item.quantity_fulfilled - item.quantity)
                await self.order_item_repo.save_no_commit(order_item)

        await self.repo.save_no_commit(shipment)
        await self.session.commit()
        await self.session.refresh(shipment)
        return shipment
