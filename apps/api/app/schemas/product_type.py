from datetime import datetime

from pydantic import BaseModel, Field


class ProductTypeCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    description: str | None = None
    is_active: bool = True


class ProductTypeUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    description: str | None = None
    is_active: bool | None = None


class ProductTypeItem(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class ProductTypeListResponse(BaseModel):
    items: list[ProductTypeItem]
    total: int
    limit: int
    offset: int


class ProductTypeAttributeConfig(BaseModel):
    attribute_id: str
    is_required: bool = False
    sort_order: int = 0


class ProductTypeAttributesRequest(BaseModel):
    attributes: list[ProductTypeAttributeConfig] = Field(default_factory=list)


class ProductTypeAttributeItem(BaseModel):
    attribute_id: str
    name: str
    code: str
    is_required: bool
    sort_order: int
