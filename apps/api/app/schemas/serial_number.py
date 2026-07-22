from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SerialStatus(str, Enum):
    available = "available"
    reserved = "reserved"
    sold = "sold"
    returned = "returned"
    damaged = "damaged"


class SerialNumberCreateRequest(BaseModel):
    product_id: str
    variant_id: str | None = None
    warehouse_id: str
    batch_id: str | None = None
    bin_id: str | None = None
    serial: str = Field(..., min_length=1, max_length=150)
    status: SerialStatus = SerialStatus.available
    notes: str | None = None


class SerialNumberBulkImportRequest(BaseModel):
    product_id: str
    variant_id: str | None = None
    warehouse_id: str
    batch_id: str | None = None
    bin_id: str | None = None
    serials: list[str] = Field(..., min_length=1)


class SerialNumberUpdateRequest(BaseModel):
    batch_id: str | None = None
    bin_id: str | None = None
    status: SerialStatus | None = None
    notes: str | None = None


class SerialNumberItem(BaseModel):
    id: str
    inventory_id: str
    product_id: str
    variant_id: str | None = None
    warehouse_id: str
    batch_id: str | None = None
    bin_id: str | None = None
    serial: str
    status: SerialStatus
    sold_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class SerialNumberListResponse(BaseModel):
    items: list[SerialNumberItem]
    total: int
    limit: int
    offset: int


class BulkDeleteRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1)
