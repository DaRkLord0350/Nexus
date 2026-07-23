from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PickupStatus(str, Enum):
    scheduled = "scheduled"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"
    missed = "missed"


class PickupCreateRequest(BaseModel):
    warehouse_id: str
    shipping_provider_id: str | None = None
    scheduled_date: datetime
    time_slot: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    notes: str | None = None
    shipment_ids: list[str] = Field(default_factory=list)


class PickupRescheduleRequest(BaseModel):
    scheduled_date: datetime
    time_slot: str | None = None


class PickupCancelRequest(BaseModel):
    reason: str | None = None


class PickupRead(BaseModel):
    id: str
    pickup_number: str
    warehouse_id: str
    shipping_provider_id: str | None = None
    status: PickupStatus
    scheduled_date: datetime
    time_slot: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    notes: str | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancelled_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PickupListResponse(BaseModel):
    items: list[PickupRead]
    total: int
    limit: int
    offset: int
