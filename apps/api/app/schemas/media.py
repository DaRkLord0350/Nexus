from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MediaType(str, Enum):
    image = "image"
    video = "video"
    pdf = "pdf"
    model_3d = "model_3d"


class StorageProvider(str, Enum):
    local = "local"
    s3 = "s3"


class MediaItem(BaseModel):
    id: str
    product_id: str | None = None
    variant_id: str | None = None
    media_type: MediaType
    object_key: str
    storage_provider: StorageProvider
    bucket: str | None = None
    content_type: str
    size_bytes: int
    checksum: str | None = None
    thumbnail_key: str | None = None
    alt_text: str | None = None
    is_primary: bool
    sort_order: int
    uploaded_by: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class MediaListResponse(BaseModel):
    items: list[MediaItem]


class MediaUpdateRequest(BaseModel):
    alt_text: str | None = None
    is_primary: bool | None = None
    sort_order: int | None = None


class SignedUrlResponse(BaseModel):
    signed_url: str


class ReorderRequest(BaseModel):
    media_ids: list[str] = Field(..., min_length=1)
