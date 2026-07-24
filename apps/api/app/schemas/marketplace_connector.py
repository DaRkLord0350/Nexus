from datetime import datetime

from pydantic import BaseModel, Field


class MarketplaceConnectorCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=64)
    connector_type: str = Field(default="other", max_length=32)
    is_active: bool = True
    credentials: dict | None = None
    webhook_secret: str | None = None
    store_url: str | None = Field(default=None, max_length=500)
    auto_sync_products: bool = False
    auto_sync_orders: bool = False
    auto_sync_inventory: bool = False
    auto_sync_prices: bool = False
    sync_interval_minutes: int = Field(default=60, ge=5)


class MarketplaceConnectorUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    connector_type: str | None = Field(default=None, max_length=32)
    is_active: bool | None = None
    credentials: dict | None = None
    webhook_secret: str | None = None
    store_url: str | None = Field(default=None, max_length=500)
    auto_sync_products: bool | None = None
    auto_sync_orders: bool | None = None
    auto_sync_inventory: bool | None = None
    auto_sync_prices: bool | None = None
    sync_interval_minutes: int | None = Field(default=None, ge=5)


class MarketplaceConnectorRead(BaseModel):
    id: str
    name: str
    code: str
    connector_type: str
    is_active: bool
    store_url: str | None = None
    auto_sync_products: bool
    auto_sync_orders: bool
    auto_sync_inventory: bool
    auto_sync_prices: bool
    sync_interval_minutes: int
    last_sync_at: datetime | None = None
    last_sync_status: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MarketplaceConnectorListResponse(BaseModel):
    items: list[MarketplaceConnectorRead]
    total: int
    limit: int
    offset: int
