from datetime import datetime

from pydantic import BaseModel, Field


class MarketplaceWebhookRequest(BaseModel):
    """Normalized inbound webhook payload. A real integration would translate
    each marketplace's native webhook format into this shape before calling
    this endpoint (mirrors ShipmentTrackingWebhookRequest)."""

    connector_code: str = Field(..., min_length=1, max_length=64)
    event_type: str = Field(..., min_length=1, max_length=64)
    payload: dict


class MarketplaceWebhookEventRead(BaseModel):
    id: str
    marketplace_connector_id: str
    event_type: str
    status: str
    retry_count: int
    next_retry_at: datetime | None = None
    last_error: str | None = None
    received_at: datetime
    processed_at: datetime | None = None

    model_config = {"from_attributes": True}


class MarketplaceWebhookEventListResponse(BaseModel):
    items: list[MarketplaceWebhookEventRead]
    total: int
    limit: int
    offset: int
