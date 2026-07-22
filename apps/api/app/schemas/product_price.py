from datetime import datetime

from pydantic import BaseModel, Field


class ProductPriceCreateRequest(BaseModel):
    product_id: str
    variant_id: str | None = None
    currency: str = Field(..., min_length=3, max_length=3)
    mrp: float | None = None
    selling_price: float = Field(..., ge=0)
    cost_price: float | None = None
    compare_price: float | None = None
    min_price: float | None = None
    max_price: float | None = None
    customer_group: str | None = None
    region: str | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    is_active: bool = True


class ProductPriceUpdateRequest(BaseModel):
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    mrp: float | None = None
    selling_price: float | None = Field(default=None, ge=0)
    cost_price: float | None = None
    compare_price: float | None = None
    min_price: float | None = None
    max_price: float | None = None
    customer_group: str | None = None
    region: str | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    is_active: bool | None = None


class ProductPriceItem(BaseModel):
    id: str
    product_id: str
    variant_id: str | None = None
    currency: str
    mrp: float | None = None
    selling_price: float
    cost_price: float | None = None
    compare_price: float | None = None
    min_price: float | None = None
    max_price: float | None = None
    customer_group: str | None = None
    region: str | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class ProductPriceListResponse(BaseModel):
    items: list[ProductPriceItem]
    total: int
    limit: int
    offset: int


class BulkDeleteRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1)
