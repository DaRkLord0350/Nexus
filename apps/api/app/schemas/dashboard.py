from datetime import datetime
from pydantic import BaseModel


class DashboardMetric(BaseModel):
    id: str
    title: str
    value: int
    subtitle: str | None = None


class DashboardActivityItem(BaseModel):
    id: str
    user_id: str
    user_name: str
    device_name: str | None
    ip_address: str | None
    last_active_at: datetime
    status: str


class DashboardSummary(BaseModel):
    week_start: datetime
    generated_at: datetime


class OrganizationBrief(BaseModel):
    id: str
    name: str
    slug: str
    status: str


class DashboardResponse(BaseModel):
    organization: OrganizationBrief | None
    metrics: list[DashboardMetric]
    recent_activity: list[DashboardActivityItem]
    summary: DashboardSummary

    class Config:
        orm_mode = True
