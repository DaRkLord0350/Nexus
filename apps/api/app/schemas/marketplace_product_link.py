from datetime import datetime

from pydantic import BaseModel, Field


class MarketplaceProductLinkCreateRequest(BaseModel):
    marketplace_connector_id: str
    product_id: str
    external_id: str | None = Field(default=None, max_length=255)
    external_sku: str | None = Field(default=None, max_length=100)


class MarketplaceProductLinkRead(BaseModel):
    id: str
    marketplace_connector_id: str
    product_id: str
    external_id: str | None = None
    external_sku: str | None = None
    external_url: str | None = None
    sync_status: str
    last_synced_at: datetime | None = None
    last_error: str | None = None
    last_synced_price: float | None = None
    last_synced_quantity: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MarketplaceProductLinkListResponse(BaseModel):
    items: list[MarketplaceProductLinkRead]
    total: int
    limit: int
    offset: int
