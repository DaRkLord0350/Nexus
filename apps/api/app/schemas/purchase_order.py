from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PurchaseOrderStatus(str, Enum):
    draft = "draft"
    sent = "sent"
    partially_received = "partially_received"
    received = "received"
    cancelled = "cancelled"


class PurchaseOrderLineItemInput(BaseModel):
    product_id: str
    variant_id: str | None = None
    quantity_ordered: int = Field(..., gt=0)
    unit_cost: float = Field(default=0, ge=0)
    tax_rate: float | None = None
    notes: str | None = None


class PurchaseOrderCreateRequest(BaseModel):
    po_number: str | None = Field(default=None, max_length=50)
    supplier_name: str = Field(..., min_length=1, max_length=255)
    supplier_email: str | None = None
    supplier_phone: str | None = None
    warehouse_id: str
    currency: str = Field(default="USD", min_length=3, max_length=3)
    tax_amount: float = Field(default=0, ge=0)
    shipping_amount: float = Field(default=0, ge=0)
    expected_date: datetime | None = None
    notes: str | None = None
    items: list[PurchaseOrderLineItemInput] = Field(default_factory=list)


class PurchaseOrderUpdateRequest(BaseModel):
    supplier_name: str | None = Field(default=None, min_length=1, max_length=255)
    supplier_email: str | None = None
    supplier_phone: str | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    tax_amount: float | None = Field(default=None, ge=0)
    shipping_amount: float | None = Field(default=None, ge=0)
    expected_date: datetime | None = None
    notes: str | None = None


class PurchaseOrderLineItem(BaseModel):
    id: str
    purchase_order_id: str
    product_id: str
    variant_id: str | None = None
    quantity_ordered: int
    quantity_received: int
    unit_cost: float
    tax_rate: float | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class PurchaseOrderRead(BaseModel):
    id: str
    po_number: str
    supplier_name: str
    supplier_email: str | None = None
    supplier_phone: str | None = None
    warehouse_id: str
    status: PurchaseOrderStatus
    currency: str
    subtotal: float
    tax_amount: float
    shipping_amount: float
    total: float
    expected_date: datetime | None = None
    sent_at: datetime | None = None
    received_at: datetime | None = None
    cancelled_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class PurchaseOrderDetail(PurchaseOrderRead):
    items: list[PurchaseOrderLineItem] = Field(default_factory=list)


class PurchaseOrderListResponse(BaseModel):
    items: list[PurchaseOrderRead]
    total: int
    limit: int
    offset: int


class BulkDeleteRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1)
