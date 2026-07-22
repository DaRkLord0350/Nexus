from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ChannelType(str, Enum):
    online_store = "online_store"
    pos = "pos"
    mobile_app = "mobile_app"
    marketplace = "marketplace"
    social = "social"
    other = "other"


class ChannelCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=64)
    channel_type: ChannelType = ChannelType.online_store
    is_active: bool = True
    is_default: bool = False


class ChannelUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=64)
    channel_type: ChannelType | None = None
    is_active: bool | None = None
    is_default: bool | None = None


class ChannelItem(BaseModel):
    id: str
    name: str
    code: str
    channel_type: ChannelType
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class ChannelListResponse(BaseModel):
    items: list[ChannelItem]
    total: int
    limit: int
    offset: int


class ProductChannelItem(BaseModel):
    channel_id: str
    name: str
    code: str
    channel_type: ChannelType
    is_published: bool
    published_at: datetime | None = None


class ProductChannelsRequest(BaseModel):
    channel_ids: list[str] = Field(default_factory=list)
