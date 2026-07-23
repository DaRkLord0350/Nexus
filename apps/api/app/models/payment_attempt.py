from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class PaymentAttemptStatus(str, PyEnum):
    pending = "pending"
    authorized = "authorized"
    captured = "captured"
    failed = "failed"
    refunded = "refunded"
    cancelled = "cancelled"


class PaymentAttempt(Base, TimestampMixin, TenantMixin):
    __tablename__ = "payment_attempts"
    __table_args__ = (
        UniqueConstraint("organization_id", "idempotency_key", name="uq_payment_attempt_organization_idempotency_key"),
    )

    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    method = Column(String(32), nullable=False)
    gateway = Column(String(64), nullable=False, default="manual")
    status = Column(Enum(PaymentAttemptStatus, native_enum=False), nullable=False, default=PaymentAttemptStatus.pending, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    gateway_reference = Column(String(255), nullable=True)
    gateway_response = Column(Text, nullable=True)
    failure_reason = Column(Text, nullable=True)
    idempotency_key = Column(String(128), nullable=True)
    initiated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
