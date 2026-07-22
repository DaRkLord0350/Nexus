from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AttributeInputType(str, Enum):
    select = "select"
    text = "text"
    number = "number"
    boolean = "boolean"


class AttributeCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=255)
    input_type: AttributeInputType = AttributeInputType.select
    is_variant_attribute: bool = True
    sort_order: int = 0
    is_active: bool = True


class AttributeUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=255)
    input_type: AttributeInputType | None = None
    is_variant_attribute: bool | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class AttributeItem(BaseModel):
    id: str
    name: str
    code: str
    input_type: AttributeInputType
    is_variant_attribute: bool
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class AttributeListResponse(BaseModel):
    items: list[AttributeItem]
    total: int
    limit: int
    offset: int


class AttributeValueCreateRequest(BaseModel):
    value: str = Field(..., min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    color_hex: str | None = Field(default=None, max_length=16)
    sort_order: int = 0
    is_active: bool = True


class AttributeValueUpdateRequest(BaseModel):
    value: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    color_hex: str | None = Field(default=None, max_length=16)
    sort_order: int | None = None
    is_active: bool | None = None


class AttributeValueItem(BaseModel):
    id: str
    attribute_id: str
    value: str
    slug: str
    color_hex: str | None = None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class BulkDeleteRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1)
