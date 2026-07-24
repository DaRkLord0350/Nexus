from datetime import datetime

from pydantic import BaseModel


class MarketplaceOrderLinkRead(BaseModel):
    id: str
    marketplace_connector_id: str
    order_id: str | None = None
    external_order_id: str
    external_order_number: str | None = None
    status: str
    last_error: str | None = None
    imported_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MarketplaceOrderLinkListResponse(BaseModel):
    items: list[MarketplaceOrderLinkRead]
    total: int
    limit: int
    offset: int
