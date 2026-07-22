from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class StockAdjustmentReason(str, Enum):
    damage = "damage"
    lost = "lost"
    found = "found"
    audit = "audit"
    manual = "manual"


class StockAdjustmentCreateRequest(BaseModel):
    adjustment_number: str | None = Field(default=None, max_length=50)
    product_id: str
    variant_id: str | None = None
    warehouse_id: str
    bin_id: str | None = None
    quantity_delta: int
    reason: StockAdjustmentReason = StockAdjustmentReason.manual
    notes: str | None = None


class StockAdjustmentItem(BaseModel):
    id: str
    adjustment_number: str
    inventory_id: str
    product_id: str
    variant_id: str | None = None
    warehouse_id: str
    bin_id: str | None = None
    quantity_delta: int
    reason: StockAdjustmentReason
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class StockAdjustmentListResponse(BaseModel):
    items: list[StockAdjustmentItem]
    total: int
    limit: int
    offset: int
