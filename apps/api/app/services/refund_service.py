from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refund import Refund, RefundStatus
from app.models.refund_item import RefundItem
from app.repositories.order_repository import OrderRepository
from app.repositories.refund_repository import RefundItemRepository, RefundRepository
from app.repositories.return_request_repository import ReturnRequestRepository
from app.services.payment_service import PaymentService

ALLOWED_TRANSITIONS: dict[RefundStatus, set[RefundStatus]] = {
    RefundStatus.requested: {RefundStatus.approved, RefundStatus.rejected},
    RefundStatus.approved: {RefundStatus.processing, RefundStatus.completed, RefundStatus.failed},
    RefundStatus.processing: {RefundStatus.completed, RefundStatus.failed},
    RefundStatus.rejected: set(),
    RefundStatus.completed: set(),
    RefundStatus.failed: set(),
}


class RefundService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = RefundRepository(session, organization_id, is_superuser)
        self.item_repo = RefundItemRepository(session, organization_id, is_superuser)
        self.order_repo = OrderRepository(session, organization_id, is_superuser)
        self.return_repo = ReturnRequestRepository(session, organization_id, is_superuser)
        self.payment_service = PaymentService(session, organization_id, is_superuser)

    def _generate_refund_number(self) -> str:
        return f"REF-{uuid4().hex[:10].upper()}"

    async def _available_to_refund(self, order) -> float:
        pending = await self.repo.sum_refunded_for_order(order.id)
        return round(order.amount_paid - order.amount_refunded - pending, 2)

    async def create_refund_request(self, data, requested_by: str | None = None) -> Refund:
        order = await self.order_repo.get_by_id(data.order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        if data.return_request_id:
            return_request = await self.return_repo.get_by_id(data.return_request_id)
            if not return_request or return_request.order_id != order.id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Return request not found for this order.")

        available = await self._available_to_refund(order)
        if data.amount > available:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Only {available} is available to refund for this order.")

        refund_number = self._generate_refund_number()
        while await self.repo.get_by_number(refund_number):
            refund_number = self._generate_refund_number()

        refund = Refund(
            refund_number=refund_number,
            order_id=order.id,
            return_request_id=data.return_request_id,
            customer_id=order.customer_id,
            method=data.method,
            status=RefundStatus.requested,
            amount=data.amount,
            currency=order.currency,
            reason=data.reason,
            requested_by=requested_by,
        )
        self.repo._add_tenant_on_create(refund)
        refund = await self.repo.save_no_commit(refund)

        for item_data in data.items:
            item = RefundItem(refund_id=refund.id, order_item_id=item_data.order_item_id, quantity=item_data.quantity, amount=item_data.amount)
            await self.item_repo.create_no_commit(item)

        await self.session.commit()
        await self.session.refresh(refund)
        return refund

    async def _get_or_404(self, refund_id: str) -> Refund:
        refund = await self.repo.get_by_id(refund_id)
        if not refund:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refund not found.")
        return refund

    async def get_refund(self, refund_id: str) -> Refund | None:
        return await self.repo.get_by_id(refund_id)

    async def get_items(self, refund_id: str) -> list[RefundItem]:
        return await self.item_repo.list_for_refund(refund_id)

    async def list_refunds(
        self,
        order_id: str | None = None,
        customer_id: str | None = None,
        status_filter: RefundStatus | None = None,
        q: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Refund], int]:
        items = await self.repo.list(order_id, customer_id, status_filter, q, sort_by, sort_order, limit, offset)
        total = await self.repo.count(order_id, customer_id, status_filter, q)
        return items, total

    async def _transition(self, refund_id: str, new_status: RefundStatus) -> Refund:
        refund = await self._get_or_404(refund_id)
        allowed = ALLOWED_TRANSITIONS.get(refund.status, set())
        if new_status not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot move a refund from '{refund.status.value}' to '{new_status.value}'.",
            )
        refund.status = new_status
        return await self.repo.save(refund)

    async def approve_refund(self, refund_id: str, changed_by: str | None = None) -> Refund:
        refund = await self._transition(refund_id, RefundStatus.approved)
        refund.approved_by = changed_by
        refund.approved_at = datetime.utcnow()
        return await self.repo.save(refund)

    async def reject_refund(self, refund_id: str, changed_by: str | None = None, reason: str | None = None) -> Refund:
        refund = await self._transition(refund_id, RefundStatus.rejected)
        refund.rejected_reason = reason
        return await self.repo.save(refund)

    async def complete_refund(self, refund_id: str, changed_by: str | None = None) -> Refund:
        refund = await self._get_or_404(refund_id)
        allowed = ALLOWED_TRANSITIONS.get(refund.status, set())
        if RefundStatus.completed not in allowed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot complete a refund in '{refund.status.value}' status.")

        attempt = await self.payment_service.refund_payment(
            refund.order_id, refund.amount, reason=refund.reason or f"Refund {refund.refund_number}", created_by=changed_by,
        )
        refund.payment_attempt_id = attempt.id
        refund.status = RefundStatus.completed
        refund.processed_at = datetime.utcnow()
        return await self.repo.save(refund)

    async def fail_refund(self, refund_id: str, changed_by: str | None = None, reason: str | None = None) -> Refund:
        refund = await self._transition(refund_id, RefundStatus.failed)
        refund.rejected_reason = reason
        return await self.repo.save(refund)
