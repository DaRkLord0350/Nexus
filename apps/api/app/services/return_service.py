from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory_transaction import InventoryTransactionType
from app.models.order import OrderStatus
from app.models.return_item import ReturnItem, ReturnItemCondition
from app.models.return_request import ReturnRequest, ReturnResolution, ReturnStatus
from app.repositories.order_repository import OrderItemRepository, OrderRepository
from app.repositories.return_request_repository import ReturnItemRepository, ReturnRequestRepository
from app.services.stock_movement_service import StockMovementService

ALLOWED_TRANSITIONS: dict[ReturnStatus, set[ReturnStatus]] = {
    ReturnStatus.requested: {ReturnStatus.approved, ReturnStatus.rejected, ReturnStatus.cancelled},
    ReturnStatus.approved: {ReturnStatus.awaiting_pickup, ReturnStatus.in_transit, ReturnStatus.received, ReturnStatus.cancelled},
    ReturnStatus.awaiting_pickup: {ReturnStatus.in_transit, ReturnStatus.received, ReturnStatus.cancelled},
    ReturnStatus.in_transit: {ReturnStatus.received, ReturnStatus.cancelled},
    ReturnStatus.received: {ReturnStatus.inspecting, ReturnStatus.cancelled},
    ReturnStatus.inspecting: {ReturnStatus.completed, ReturnStatus.rejected},
    ReturnStatus.rejected: set(),
    ReturnStatus.completed: set(),
    ReturnStatus.cancelled: set(),
}

# Conditions that still qualify for resale; anything else lands in damaged stock.
SELLABLE_CONDITIONS = {ReturnItemCondition.unopened, ReturnItemCondition.opened}


class ReturnService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = ReturnRequestRepository(session, organization_id, is_superuser)
        self.item_repo = ReturnItemRepository(session, organization_id, is_superuser)
        self.order_repo = OrderRepository(session, organization_id, is_superuser)
        self.order_item_repo = OrderItemRepository(session, organization_id, is_superuser)
        self.stock_service = StockMovementService(session, organization_id, is_superuser)

    def _generate_return_number(self) -> str:
        return f"RET-{uuid4().hex[:10].upper()}"

    async def create_return_request(self, data, customer_id: str | None = None, created_by: str | None = None) -> ReturnRequest:
        order = await self.order_repo.get_by_id(data.order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
        if order.status != OrderStatus.delivered:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only delivered orders can be returned.")
        if customer_id and order.customer_id != customer_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This order does not belong to you.")

        resolved_items = []
        for item_data in data.items:
            order_item = await self.order_item_repo.get_by_id(item_data.order_item_id)
            if not order_item or order_item.order_id != order.id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order item not found on this order.")

            already_returned = await self.item_repo.sum_returned_for_order_item(order_item.id)
            remaining = order_item.quantity - already_returned
            if item_data.quantity > remaining:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Only {remaining} unit(s) of {order_item.product_name} remain eligible for return.")

            resolved_items.append(ReturnItem(
                order_item_id=order_item.id,
                product_id=order_item.product_id,
                variant_id=order_item.variant_id,
                quantity=item_data.quantity,
                reason_code=item_data.reason_code or data.reason_code,
                image_urls=",".join(item_data.image_urls) if item_data.image_urls else None,
            ))

        return_number = self._generate_return_number()
        while await self.repo.get_by_number(return_number):
            return_number = self._generate_return_number()

        return_request = ReturnRequest(
            return_number=return_number,
            order_id=order.id,
            customer_id=order.customer_id,
            status=ReturnStatus.requested,
            reason_code=data.reason_code,
            reason_notes=data.reason_notes,
            created_by=created_by,
        )
        self.repo._add_tenant_on_create(return_request)
        return_request = await self.repo.save_no_commit(return_request)

        for item in resolved_items:
            item.return_request_id = return_request.id
            await self.item_repo.create_no_commit(item)

        await self.session.commit()
        await self.session.refresh(return_request)
        return return_request

    async def _get_or_404(self, return_id: str) -> ReturnRequest:
        return_request = await self.repo.get_by_id(return_id)
        if not return_request:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return request not found.")
        return return_request

    async def get_return(self, return_id: str) -> ReturnRequest | None:
        return await self.repo.get_by_id(return_id)

    async def get_items(self, return_id: str) -> list[ReturnItem]:
        return await self.item_repo.list_for_return(return_id)

    async def list_returns(
        self,
        order_id: str | None = None,
        customer_id: str | None = None,
        status_filter: ReturnStatus | None = None,
        q: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ReturnRequest], int]:
        items = await self.repo.list(order_id, customer_id, status_filter, q, sort_by, sort_order, limit, offset)
        total = await self.repo.count(order_id, customer_id, status_filter, q)
        return items, total

    async def _transition(self, return_id: str, new_status: ReturnStatus) -> ReturnRequest:
        return_request = await self._get_or_404(return_id)
        allowed = ALLOWED_TRANSITIONS.get(return_request.status, set())
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot move a return from '{return_request.status.value}' to '{new_status.value}'.",
            )
        return_request.status = new_status
        return await self.repo.save(return_request)

    async def approve_return(self, return_id: str, changed_by: str | None = None, resolution: ReturnResolution | None = None) -> ReturnRequest:
        return_request = await self._transition(return_id, ReturnStatus.approved)
        return_request.approved_by = changed_by
        return_request.approved_at = datetime.utcnow()
        if resolution:
            return_request.resolution = resolution
        return await self.repo.save(return_request)

    async def reject_return(self, return_id: str, changed_by: str | None = None, reason: str | None = None) -> ReturnRequest:
        return_request = await self._get_or_404(return_id)
        allowed = ALLOWED_TRANSITIONS.get(return_request.status, set())
        if ReturnStatus.rejected not in allowed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot reject a return in '{return_request.status.value}' status.")
        return_request.status = ReturnStatus.rejected
        return_request.rejected_reason = reason
        return await self.repo.save(return_request)

    async def mark_awaiting_pickup(self, return_id: str) -> ReturnRequest:
        return await self._transition(return_id, ReturnStatus.awaiting_pickup)

    async def mark_in_transit(self, return_id: str) -> ReturnRequest:
        return await self._transition(return_id, ReturnStatus.in_transit)

    async def mark_received(self, return_id: str, warehouse_id: str | None = None) -> ReturnRequest:
        return_request = await self._transition(return_id, ReturnStatus.received)
        if warehouse_id:
            return_request.warehouse_id = warehouse_id
            return_request = await self.repo.save(return_request)
        return return_request

    async def start_inspection(self, return_id: str, changed_by: str | None = None) -> ReturnRequest:
        return_request = await self._transition(return_id, ReturnStatus.inspecting)
        return_request.inspected_by = changed_by
        return_request.inspected_at = datetime.utcnow()
        return await self.repo.save(return_request)

    async def update_item_inspection(self, return_id: str, item_id: str, condition: ReturnItemCondition, reason_code: str | None = None) -> ReturnItem:
        return_request = await self._get_or_404(return_id)
        if return_request.status != ReturnStatus.inspecting:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Items can only be inspected while the return is in the inspecting status.")

        item = await self.item_repo.get_by_id(item_id)
        if not item or item.return_request_id != return_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return item not found.")

        item.condition = condition
        if reason_code:
            item.reason_code = reason_code
        return await self.item_repo.save(item)

    async def cancel_return(self, return_id: str, reason: str | None = None) -> ReturnRequest:
        return_request = await self._get_or_404(return_id)
        allowed = ALLOWED_TRANSITIONS.get(return_request.status, set())
        if ReturnStatus.cancelled not in allowed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot cancel a return in '{return_request.status.value}' status.")
        return_request.status = ReturnStatus.cancelled
        return_request.cancelled_at = datetime.utcnow()
        return_request.rejected_reason = reason
        return await self.repo.save(return_request)

    async def complete_return(self, return_id: str, resolution: ReturnResolution, restock: bool = True, changed_by: str | None = None) -> ReturnRequest:
        return_request = await self._transition(return_id, ReturnStatus.completed)
        return_request.resolution = resolution
        return_request.completed_at = datetime.utcnow()

        items = await self.item_repo.list_for_return(return_id)
        for item in items:
            order_item = await self.order_item_repo.get_by_id(item.order_item_id)
            if order_item:
                order_item.quantity_returned = order_item.quantity_returned + item.quantity
                await self.order_item_repo.save(order_item)

            if restock and return_request.warehouse_id:
                field = "quantity_available" if (item.condition in SELLABLE_CONDITIONS or item.condition is None) else "quantity_damaged"
                await self.stock_service.apply_movement(
                    product_id=item.product_id, variant_id=item.variant_id, warehouse_id=return_request.warehouse_id,
                    transaction_type=InventoryTransactionType.return_, quantity_delta=item.quantity, field=field,
                    reference_type="return_request", reference_id=return_request.id, user_id=changed_by,
                )
                item.restocked = True
                item.restocked_quantity = item.quantity
                await self.item_repo.save(item)

        return await self.repo.save(return_request)
