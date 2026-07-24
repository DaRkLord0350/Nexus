from datetime import datetime

from pydantic import BaseModel


class MarketplaceSyncLogRead(BaseModel):
    id: str
    marketplace_connector_id: str
    sync_type: str
    status: str
    triggered_by: str
    items_processed: int
    items_succeeded: int
    items_failed: int
    started_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MarketplaceSyncLogListResponse(BaseModel):
    items: list[MarketplaceSyncLogRead]
    total: int
    limit: int
    offset: int
