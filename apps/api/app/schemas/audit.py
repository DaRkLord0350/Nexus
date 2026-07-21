from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogItem(BaseModel):
    id: str
    organization_id: str
    user_id: str | None = None
    action: str
    module: str
    entity: str | None = None
    entity_id: str | None = None
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str | None = None
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class AuditLogListResponse(BaseModel):
    items: list[AuditLogItem]
    total: int
    limit: int
    offset: int
