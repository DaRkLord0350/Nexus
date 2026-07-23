from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PaymentAttemptStatus(str, Enum):
    pending = "pending"
    authorized = "authorized"
    captured = "captured"
    failed = "failed"
    refunded = "refunded"
    cancelled = "cancelled"


class PaymentAttemptCreateRequest(BaseModel):
    method: str = Field(..., min_length=1, max_length=32)
    gateway: str | None = Field(default=None, max_length=64)
    amount: float = Field(..., gt=0)
    idempotency_key: str | None = Field(default=None, max_length=128)


class PaymentAttemptRead(BaseModel):
    id: str
    order_id: str
    method: str
    gateway: str
    status: PaymentAttemptStatus
    amount: float
    currency: str
    gateway_reference: str | None = None
    failure_reason: str | None = None
    idempotency_key: str | None = None
    initiated_at: datetime
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RefundPaymentRequest(BaseModel):
    amount: float = Field(..., gt=0)
    reason: str | None = None
