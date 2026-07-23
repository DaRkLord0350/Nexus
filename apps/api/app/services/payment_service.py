from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import PaymentStatus
from app.models.payment_attempt import PaymentAttempt, PaymentAttemptStatus
from app.repositories.order_repository import OrderRepository
from app.repositories.payment_attempt_repository import PaymentAttemptRepository


class PaymentService:
    """Payment gateway abstraction. COD is authorized at order time and
    captured on delivery (see OrderService._transition). Other methods are
    routed through a mock adapter that always succeeds synchronously until a
    real gateway (Stripe/Razorpay/PayPal/etc) is wired in — swap
    `_call_gateway` for a real integration without touching callers."""

    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = PaymentAttemptRepository(session, organization_id, is_superuser)
        self.order_repo = OrderRepository(session, organization_id, is_superuser)

    async def _get_order_or_404(self, order_id: str):
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
        return order

    async def _call_gateway(self, method: str, amount: float) -> tuple[PaymentAttemptStatus, str | None, str | None]:
        if method == "cod":
            return PaymentAttemptStatus.authorized, None, None
        if method == "wallet" and amount <= 0:
            return PaymentAttemptStatus.failed, None, "Invalid wallet amount."
        return PaymentAttemptStatus.captured, f"MOCK-{uuid4().hex[:12].upper()}", None

    async def create_payment_attempt(self, order_id: str, data, created_by: str | None = None) -> PaymentAttempt:
        order = await self._get_order_or_404(order_id)

        if data.idempotency_key:
            existing = await self.repo.get_by_idempotency_key(data.idempotency_key)
            if existing:
                return existing

        gateway_status, gateway_reference, failure_reason = await self._call_gateway(data.method, data.amount)

        attempt = PaymentAttempt(
            order_id=order_id,
            method=data.method,
            gateway=data.gateway or "manual",
            status=gateway_status,
            amount=data.amount,
            currency=order.currency,
            gateway_reference=gateway_reference,
            failure_reason=failure_reason,
            idempotency_key=data.idempotency_key,
            completed_at=datetime.utcnow() if gateway_status in (PaymentAttemptStatus.captured, PaymentAttemptStatus.failed) else None,
            created_by=created_by,
        )
        attempt = await self.repo.create(attempt)

        if gateway_status == PaymentAttemptStatus.captured:
            order.amount_paid = round(order.amount_paid + data.amount, 2)
            order.payment_status = PaymentStatus.paid if order.amount_paid >= order.total else PaymentStatus.partially_paid
            await self.order_repo.save(order)

        return attempt

    async def refund_payment(self, order_id: str, amount: float, reason: str | None = None, created_by: str | None = None) -> PaymentAttempt:
        order = await self._get_order_or_404(order_id)
        refundable = order.amount_paid - order.amount_refunded
        if amount > refundable:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Only {refundable} is available to refund for this order.")

        attempt = PaymentAttempt(
            order_id=order_id,
            method="refund",
            gateway="manual",
            status=PaymentAttemptStatus.refunded,
            amount=-abs(amount),
            currency=order.currency,
            failure_reason=reason,
            completed_at=datetime.utcnow(),
            created_by=created_by,
        )
        attempt = await self.repo.create(attempt)

        order.amount_refunded = round(order.amount_refunded + abs(amount), 2)
        order.payment_status = PaymentStatus.refunded if order.amount_refunded >= order.amount_paid else PaymentStatus.partially_refunded
        await self.order_repo.save(order)

        return attempt

    async def list_payment_attempts(self, order_id: str) -> list[PaymentAttempt]:
        return await self.repo.list_for_order(order_id)
