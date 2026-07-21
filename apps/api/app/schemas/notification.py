from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    success = "success"
    warning = "warning"
    error = "error"
    info = "info"


class NotificationChannel(str, Enum):
    in_app = "in_app"
    email = "email"
    database = "database"
    sms = "sms"


class NotificationBase(BaseModel):
    title: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class NotificationCreateRequest(NotificationBase):
    type: NotificationType = NotificationType.info
    channels: list[NotificationChannel] = Field(default_factory=lambda: [NotificationChannel.in_app, NotificationChannel.email])
    actor_id: str | None = None
    metadata: dict[str, Any] | None = None


class NotificationPreferenceItem(BaseModel):
    channel: NotificationChannel
    enabled: bool


class NotificationPreferenceUpdateRequest(BaseModel):
    channel: NotificationChannel
    enabled: bool


class NotificationItem(BaseModel):
    id: str
    user_id: str
    actor_id: str | None
    title: str
    message: str
    type: NotificationType
    channel: NotificationChannel
    metadata: dict[str, Any] | None = Field(default=None, alias="payload")
    is_read: bool
    read_at: datetime | None
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class NotificationListResponse(BaseModel):
    notifications: list[NotificationItem]


class UnreadCountResponse(BaseModel):
    unread_count: int
