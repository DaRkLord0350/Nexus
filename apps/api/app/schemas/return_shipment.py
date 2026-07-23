from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ReturnShipmentStatus(str, Enum):
    pending = "pending"
    label_generated = "label_generated"
    reverse_pickup_scheduled = "reverse_pickup_scheduled"
    in_transit = "in_transit"
    received = "received"
    cancelled = "cancelled"


class ReturnShipmentCreateRequest(BaseModel):
    return_request_id: str
    warehouse_id: str
    shipping_provider_id: str | None = None
    notes: str | None = None


class ReturnShipmentSchedulePickupRequest(BaseModel):
    scheduled_at: datetime


class ReturnShipmentCancelRequest(BaseModel):
    reason: str | None = None


class ReturnShipmentRead(BaseModel):
    id: str
    return_shipment_number: str
    return_request_id: str
    warehouse_id: str
    shipping_provider_id: str | None = None
    status: ReturnShipmentStatus
    tracking_number: str | None = None
    carrier_name: str | None = None
    pickup_contact_name: str | None = None
    pickup_contact_phone: str | None = None
    pickup_line1: str | None = None
    pickup_city: str | None = None
    pickup_state: str | None = None
    pickup_postal_code: str | None = None
    pickup_country: str | None = None
    reverse_pickup_scheduled_at: datetime | None = None
    reverse_pickup_completed_at: datetime | None = None
    received_at: datetime | None = None
    cancelled_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReturnShipmentListResponse(BaseModel):
    items: list[ReturnShipmentRead]
    total: int
    limit: int
    offset: int
