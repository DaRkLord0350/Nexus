from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class BrandStatus(str, Enum):
    draft = "draft"
    active = "active"
    archived = "archived"


class BrandCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    description: str | None = None
    logo_url: str | None = None
    website: str | None = None
    is_featured: bool = False
    status: BrandStatus = BrandStatus.active
    seo_title: str | None = None
    seo_description: str | None = None
    seo_keywords: str | None = None
    og_image_url: str | None = None
    canonical_url: str | None = None
    no_index: bool = False


class BrandUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    description: str | None = None
    logo_url: str | None = None
    website: str | None = None
    is_featured: bool | None = None
    status: BrandStatus | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    seo_keywords: str | None = None
    og_image_url: str | None = None
    canonical_url: str | None = None
    no_index: bool | None = None


class BrandItem(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None = None
    logo_url: str | None = None
    website: str | None = None
    is_featured: bool
    status: BrandStatus
    seo_title: str | None = None
    seo_description: str | None = None
    seo_keywords: str | None = None
    og_image_url: str | None = None
    canonical_url: str | None = None
    no_index: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class BrandListResponse(BaseModel):
    items: list[BrandItem]
    total: int
    limit: int
    offset: int


class BulkDeleteRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1)
