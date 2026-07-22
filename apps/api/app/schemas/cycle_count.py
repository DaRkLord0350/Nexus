from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CycleCountStatus(str, Enum):
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class CycleCountItemInput(BaseModel):
    product_id: str
    variant_id: str | None = None
    bin_id: str | None = None
    notes: str | None = None


class CycleCountCreateRequest(BaseModel):
    count_number: str | None = Field(default=None, max_length=50)
    warehouse_id: str
    zone_id: str | None = None
    scheduled_date: datetime | None = None
    assigned_to: str | None = None
    notes: str | None = None
    items: list[CycleCountItemInput] = Field(default_factory=list)


class CycleCountRecordRequest(BaseModel):
    actual_quantity: int = Field(..., ge=0)
    notes: str | None = None


class CycleCountLineItem(BaseModel):
    id: str
    cycle_count_id: str
    inventory_id: str
    product_id: str
    variant_id: str | None = None
    bin_id: str | None = None
    expected_quantity: int
    actual_quantity: int | None = None
    variance: int | None = None
    counted_at: datetime | None = None
    counted_by: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class CycleCountRead(BaseModel):
    id: str
    count_number: str
    warehouse_id: str
    zone_id: str | None = None
    status: CycleCountStatus
    scheduled_date: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    assigned_to: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class CycleCountDetail(CycleCountRead):
    items: list[CycleCountLineItem] = Field(default_factory=list)


class CycleCountListResponse(BaseModel):
    items: list[CycleCountRead]
    total: int
    limit: int
    offset: int
