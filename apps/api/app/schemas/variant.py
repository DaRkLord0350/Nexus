from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.attribute import AttributeValueItem


class VariantStatus(str, Enum):
    active = "active"
    archived = "archived"


class VariantCreateRequest(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    barcode: str | None = Field(default=None, max_length=100)
    weight: float | None = None
    weight_unit: str | None = None
    status: VariantStatus = VariantStatus.active
    is_default: bool = False
    sort_order: int = 0
    attribute_value_ids: list[str] = Field(default_factory=list)


class VariantUpdateRequest(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=100)
    barcode: str | None = None
    weight: float | None = None
    weight_unit: str | None = None
    status: VariantStatus | None = None
    is_default: bool | None = None
    sort_order: int | None = None
    attribute_value_ids: list[str] | None = None


class VariantItem(BaseModel):
    id: str
    product_id: str
    sku: str
    barcode: str | None = None
    weight: float | None = None
    weight_unit: str | None = None
    status: VariantStatus
    is_default: bool
    sort_order: int
    attribute_values: list[AttributeValueItem] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class VariantListResponse(BaseModel):
    items: list[VariantItem]
    total: int
    limit: int
    offset: int


class BulkDeleteRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1)
