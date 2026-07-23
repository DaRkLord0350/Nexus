from datetime import datetime

from pydantic import BaseModel, Field


class ShipmentTrackingEventCreateRequest(BaseModel):
    status: str = Field(..., min_length=1, max_length=32)
    description: str | None = None
    location: str | None = None
    occurred_at: datetime | None = None


class ShipmentTrackingEventRead(BaseModel):
    id: str
    shipment_id: str
    status: str
    description: str | None = None
    location: str | None = None
    occurred_at: datetime
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ShipmentTrackingWebhookRequest(BaseModel):
    """Normalized webhook payload. A real integration would translate each
    carrier's native webhook format into this shape before calling this
    endpoint (e.g. in a thin per-carrier adapter) -- no such adapters exist
    yet since no live carrier account is connected."""

    provider_code: str = Field(..., min_length=1, max_length=64)
    tracking_number: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1, max_length=32)
    description: str | None = None
    location: str | None = None
    occurred_at: datetime | None = None
