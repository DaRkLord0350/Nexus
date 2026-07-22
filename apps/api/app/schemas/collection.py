from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class CollectionType(str, Enum):
    manual = "manual"
    dynamic = "dynamic"


class CollectionStatus(str, Enum):
    draft = "draft"
    active = "active"
    archived = "archived"


class CollectionRuleCondition(BaseModel):
    field: Literal["category_id", "brand_id", "status", "is_featured", "has_variants", "tag"]
    operator: Literal["eq", "contains"] = "eq"
    value: Any


class CollectionCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    description: str | None = None
    image_url: str | None = None
    collection_type: CollectionType = CollectionType.manual
    rules: list[CollectionRuleCondition] | None = None
    status: CollectionStatus = CollectionStatus.active
    is_featured: bool = False
    sort_order: int = 0
    seo_title: str | None = None
    seo_description: str | None = None
    seo_keywords: str | None = None
    og_image_url: str | None = None
    canonical_url: str | None = None
    no_index: bool = False


class CollectionUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    description: str | None = None
    image_url: str | None = None
    collection_type: CollectionType | None = None
    rules: list[CollectionRuleCondition] | None = None
    status: CollectionStatus | None = None
    is_featured: bool | None = None
    sort_order: int | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    seo_keywords: str | None = None
    og_image_url: str | None = None
    canonical_url: str | None = None
    no_index: bool | None = None


class CollectionItem(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None = None
    image_url: str | None = None
    collection_type: CollectionType
    rules: list[CollectionRuleCondition] | None = None
    status: CollectionStatus
    is_featured: bool
    sort_order: int
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


class CollectionListResponse(BaseModel):
    items: list[CollectionItem]
    total: int
    limit: int
    offset: int


class CollectionProductsRequest(BaseModel):
    product_ids: list[str] = Field(..., min_length=1)


class BulkDeleteRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1)
