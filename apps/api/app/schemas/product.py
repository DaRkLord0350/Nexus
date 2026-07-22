from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.tag import TagItem


class ProductStatus(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class ProductCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    sku: str = Field(..., min_length=1, max_length=100)
    barcode: str | None = Field(default=None, max_length=100)
    brand_id: str | None = None
    category_id: str | None = None
    tax_class_id: str | None = None
    product_type_id: str | None = None
    description: str | None = None
    short_description: str | None = Field(default=None, max_length=500)
    status: ProductStatus = ProductStatus.draft
    seo_title: str | None = None
    seo_description: str | None = None
    seo_keywords: str | None = None
    og_image_url: str | None = None
    canonical_url: str | None = None
    no_index: bool = False
    length: float | None = None
    width: float | None = None
    height: float | None = None
    dimension_unit: str | None = None
    weight: float | None = None
    weight_unit: str | None = None
    origin_country: str | None = None
    vendor: str | None = None
    tag_names: list[str] = Field(default_factory=list)
    search_keywords: str | None = None
    track_inventory: bool = True
    allow_backorders: bool = False
    has_variants: bool = False
    is_featured: bool = False


class ProductUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    sku: str | None = Field(default=None, min_length=1, max_length=100)
    barcode: str | None = None
    brand_id: str | None = None
    category_id: str | None = None
    tax_class_id: str | None = None
    product_type_id: str | None = None
    description: str | None = None
    short_description: str | None = None
    status: ProductStatus | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    seo_keywords: str | None = None
    og_image_url: str | None = None
    canonical_url: str | None = None
    no_index: bool | None = None
    length: float | None = None
    width: float | None = None
    height: float | None = None
    dimension_unit: str | None = None
    weight: float | None = None
    weight_unit: str | None = None
    origin_country: str | None = None
    vendor: str | None = None
    tag_names: list[str] | None = None
    search_keywords: str | None = None
    track_inventory: bool | None = None
    allow_backorders: bool | None = None
    has_variants: bool | None = None
    is_featured: bool | None = None


class ProductItem(BaseModel):
    id: str
    name: str
    slug: str
    sku: str
    barcode: str | None = None
    brand_id: str | None = None
    category_id: str | None = None
    tax_class_id: str | None = None
    product_type_id: str | None = None
    description: str | None = None
    short_description: str | None = None
    status: ProductStatus
    seo_title: str | None = None
    seo_description: str | None = None
    seo_keywords: str | None = None
    og_image_url: str | None = None
    canonical_url: str | None = None
    no_index: bool
    length: float | None = None
    width: float | None = None
    height: float | None = None
    dimension_unit: str | None = None
    weight: float | None = None
    weight_unit: str | None = None
    origin_country: str | None = None
    vendor: str | None = None
    tags: list[TagItem] = Field(default_factory=list)
    search_keywords: str | None = None
    track_inventory: bool
    allow_backorders: bool
    has_variants: bool
    is_featured: bool
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class ProductListResponse(BaseModel):
    items: list[ProductItem]
    total: int
    limit: int
    offset: int


class BulkDeleteRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1)


class BulkStatusUpdateRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1)
    status: ProductStatus
