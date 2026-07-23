from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class RefundMethod(str, PyEnum):
    original_payment = "original_payment"
    store_credit = "store_credit"
    wallet = "wallet"
    bank_transfer = "bank_transfer"


class RefundStatus(str, PyEnum):
    requested = "requested"
    approved = "approved"
    rejected = "rejected"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Refund(Base, TimestampMixin, TenantMixin):
    __tablename__ = "refunds"
    __table_args__ = (
        UniqueConstraint("organization_id", "refund_number", name="uq_refund_organization_number"),
    )

    refund_number = Column(String(50), nullable=False, index=True)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False, index=True)
    return_request_id = Column(String(36), ForeignKey("return_requests.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    payment_attempt_id = Column(String(36), ForeignKey("payment_attempts.id", ondelete="SET NULL"), nullable=True, index=True)

    method = Column(Enum(RefundMethod, native_enum=False), nullable=False, default=RefundMethod.original_payment)
    status = Column(Enum(RefundStatus, native_enum=False), nullable=False, default=RefundStatus.requested, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    reason = Column(Text, nullable=True)

    requested_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_reason = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
