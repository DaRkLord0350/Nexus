from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class BatchStatus(str, Enum):
    active = "active"
    depleted = "depleted"
    expired = "expired"
    quarantined = "quarantined"
    recalled = "recalled"


class BatchCreateRequest(BaseModel):
    product_id: str
    variant_id: str | None = None
    warehouse_id: str
    batch_number: str = Field(..., min_length=1, max_length=100)
    manufactured_date: datetime | None = None
    expiry_date: datetime | None = None
    received_quantity: int = Field(default=0, ge=0)
    cost_price: float | None = None
    status: BatchStatus = BatchStatus.active


class BatchUpdateRequest(BaseModel):
    manufactured_date: datetime | None = None
    expiry_date: datetime | None = None
    remaining_quantity: int | None = Field(default=None, ge=0)
    cost_price: float | None = None
    status: BatchStatus | None = None


class BatchItem(BaseModel):
    id: str
    inventory_id: str
    product_id: str
    variant_id: str | None = None
    warehouse_id: str
    batch_number: str
    manufactured_date: datetime | None = None
    expiry_date: datetime | None = None
    received_quantity: int
    remaining_quantity: int
    status: BatchStatus
    cost_price: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class BatchListResponse(BaseModel):
    items: list[BatchItem]
    total: int
    limit: int
    offset: int


class BulkDeleteRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1)
