from datetime import datetime

from pydantic import BaseModel, Field


class CourierPerformanceStats(BaseModel):
    shipping_provider_id: str
    provider_name: str
    total_shipments: int
    delivered_count: int
    delivered_rate: float
    failed_delivery_count: int
    failed_delivery_rate: float
    cod_count: int
    cod_rate: float
    avg_transit_days: float | None = None
    total_shipping_cost: float
    avg_shipping_cost: float
    sla_met_count: int
    sla_met_rate: float | None = None


class CourierPerformanceSummary(BaseModel):
    total_shipments: int
    delivered_count: int
    delivered_rate: float
    failed_delivery_count: int
    failed_delivery_rate: float
    cod_count: int
    cod_rate: float
    total_shipping_cost: float


class CourierPerformanceResponse(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    summary: CourierPerformanceSummary
    providers: list[CourierPerformanceStats] = Field(default_factory=list)
