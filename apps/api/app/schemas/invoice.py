from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class InvoiceStatus(str, Enum):
    issued = "issued"
    paid = "paid"
    void = "void"


class InvoiceVoidRequest(BaseModel):
    reason: str | None = None


class InvoiceRead(BaseModel):
    id: str
    order_id: str
    invoice_number: str
    status: InvoiceStatus
    currency: str
    subtotal: float
    discount_amount: float
    tax_amount: float
    shipping_amount: float
    total: float
    amount_paid: float
    amount_due: float
    issued_at: datetime | None = None
    due_at: datetime | None = None
    voided_at: datetime | None = None
    void_reason: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvoiceListResponse(BaseModel):
    items: list[InvoiceRead]
    total: int
    limit: int
    offset: int
