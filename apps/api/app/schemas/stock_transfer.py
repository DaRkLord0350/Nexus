from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class StockTransferStatus(str, Enum):
    draft = "draft"
    packed = "packed"
    shipped = "shipped"
    received = "received"
    cancelled = "cancelled"


class StockTransferLineItemInput(BaseModel):
    product_id: str
    variant_id: str | None = None
    quantity_requested: int = Field(..., gt=0)
    notes: str | None = None


class StockTransferCreateRequest(BaseModel):
    transfer_number: str | None = Field(default=None, max_length=50)
    from_warehouse_id: str
    to_warehouse_id: str
    notes: str | None = None
    items: list[StockTransferLineItemInput] = Field(default_factory=list)


class StockTransferLineItem(BaseModel):
    id: str
    stock_transfer_id: str
    product_id: str
    variant_id: str | None = None
    quantity_requested: int
    quantity_shipped: int
    quantity_received: int
    batch_id: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class StockTransferRead(BaseModel):
    id: str
    transfer_number: str
    from_warehouse_id: str
    to_warehouse_id: str
    status: StockTransferStatus
    shipped_at: datetime | None = None
    received_at: datetime | None = None
    cancelled_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class StockTransferDetail(StockTransferRead):
    items: list[StockTransferLineItem] = Field(default_factory=list)


class StockTransferListResponse(BaseModel):
    items: list[StockTransferRead]
    total: int
    limit: int
    offset: int
