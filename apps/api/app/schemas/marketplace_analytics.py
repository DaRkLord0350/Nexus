from datetime import datetime

from pydantic import BaseModel, Field


class MarketplaceConnectorStats(BaseModel):
    marketplace_connector_id: str
    connector_name: str
    connector_type: str
    total_syncs: int
    successful_syncs: int
    sync_success_rate: float
    failed_syncs: int
    orders_imported: int
    orders_failed: int
    revenue_imported: float
    products_linked: int
    products_failed: int
    avg_sync_duration_seconds: float | None = None


class MarketplaceAnalyticsSummary(BaseModel):
    total_syncs: int
    sync_success_rate: float
    total_orders_imported: int
    total_revenue_imported: float
    pending_webhook_retries: int


class MarketplaceAnalyticsResponse(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    summary: MarketplaceAnalyticsSummary
    connectors: list[MarketplaceConnectorStats] = Field(default_factory=list)
