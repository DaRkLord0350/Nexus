from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class GoodsReceiptStatus(str, Enum):
    draft = "draft"
    completed = "completed"
    cancelled = "cancelled"


class GoodsReceiptItemInput(BaseModel):
    purchase_order_item_id: str | None = None
    product_id: str
    variant_id: str | None = None
    quantity_received: int = Field(..., gt=0)
    unit_cost: float | None = None
    batch_number: str | None = None
    expiry_date: datetime | None = None
    manufactured_date: datetime | None = None
    bin_id: str | None = None
    notes: str | None = None


class GoodsReceiptCreateRequest(BaseModel):
    receipt_number: str | None = Field(default=None, max_length=50)
    purchase_order_id: str | None = None
    warehouse_id: str
    received_date: datetime | None = None
    notes: str | None = None
    items: list[GoodsReceiptItemInput] = Field(default_factory=list)


class GoodsReceiptLineItem(BaseModel):
    id: str
    goods_receipt_id: str
    purchase_order_item_id: str | None = None
    product_id: str
    variant_id: str | None = None
    quantity_received: int
    unit_cost: float | None = None
    batch_number: str | None = None
    expiry_date: datetime | None = None
    manufactured_date: datetime | None = None
    bin_id: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class GoodsReceiptRead(BaseModel):
    id: str
    receipt_number: str
    purchase_order_id: str | None = None
    warehouse_id: str
    receiver_id: str | None = None
    received_date: datetime
    status: GoodsReceiptStatus
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class GoodsReceiptDetail(GoodsReceiptRead):
    items: list[GoodsReceiptLineItem] = Field(default_factory=list)


class GoodsReceiptListResponse(BaseModel):
    items: list[GoodsReceiptRead]
    total: int
    limit: int
    offset: int
