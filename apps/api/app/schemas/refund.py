from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RefundMethod(str, Enum):
    original_payment = "original_payment"
    store_credit = "store_credit"
    wallet = "wallet"
    bank_transfer = "bank_transfer"


class RefundStatus(str, Enum):
    requested = "requested"
    approved = "approved"
    rejected = "rejected"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class RefundItemInput(BaseModel):
    order_item_id: str
    quantity: int | None = Field(default=None, gt=0)
    amount: float = Field(..., ge=0)


class RefundCreateRequest(BaseModel):
    order_id: str
    return_request_id: str | None = None
    method: RefundMethod = RefundMethod.original_payment
    amount: float = Field(..., gt=0)
    reason: str | None = None
    items: list[RefundItemInput] = Field(default_factory=list)


class RefundRejectRequest(BaseModel):
    reason: str | None = None


class RefundItemRead(BaseModel):
    id: str
    refund_id: str
    order_item_id: str
    quantity: int | None = None
    amount: float
    created_at: datetime

    model_config = {"from_attributes": True}


class RefundRead(BaseModel):
    id: str
    refund_number: str
    order_id: str
    return_request_id: str | None = None
    customer_id: str
    payment_attempt_id: str | None = None
    method: RefundMethod
    status: RefundStatus
    amount: float
    currency: str
    reason: str | None = None
    requested_by: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    rejected_reason: str | None = None
    processed_at: datetime | None = None
    requested_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RefundDetail(RefundRead):
    items: list[RefundItemRead] = Field(default_factory=list)


class RefundListResponse(BaseModel):
    items: list[RefundRead]
    total: int
    limit: int
    offset: int
