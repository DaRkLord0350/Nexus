from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CategoryStatus(str, Enum):
    draft = "draft"
    active = "active"
    archived = "archived"


class CategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    description: str | None = None
    parent_id: str | None = None
    image_url: str | None = None
    banner_url: str | None = None
    sort_order: int = 0
    is_featured: bool = False
    is_visible: bool = True
    status: CategoryStatus = CategoryStatus.active
    seo_title: str | None = None
    seo_description: str | None = None
    seo_keywords: str | None = None
    og_image_url: str | None = None
    canonical_url: str | None = None
    no_index: bool = False


class CategoryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    description: str | None = None
    parent_id: str | None = Field(default=None)
    move_to_root: bool = False
    image_url: str | None = None
    banner_url: str | None = None
    sort_order: int | None = None
    is_featured: bool | None = None
    is_visible: bool | None = None
    status: CategoryStatus | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    seo_keywords: str | None = None
    og_image_url: str | None = None
    canonical_url: str | None = None
    no_index: bool | None = None


class CategoryItem(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None = None
    parent_id: str | None = None
    path: str
    image_url: str | None = None
    banner_url: str | None = None
    sort_order: int
    is_featured: bool
    is_visible: bool
    status: CategoryStatus
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


class CategoryTreeNode(CategoryItem):
    children: list["CategoryTreeNode"] = Field(default_factory=list)


CategoryTreeNode.model_rebuild()


class CategoryListResponse(BaseModel):
    items: list[CategoryItem]
    total: int
    limit: int
    offset: int


class CategoryBreadcrumbItem(BaseModel):
    id: str
    name: str
    slug: str

    model_config = {
        "from_attributes": True,
    }
