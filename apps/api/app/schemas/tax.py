from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TaxType(str, Enum):
    gst = "gst"
    vat = "vat"
    sales_tax = "sales_tax"
    other = "other"


class TaxClassCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=64)
    description: str | None = None
    is_default: bool = False
    is_active: bool = True


class TaxClassUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=64)
    description: str | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class TaxClassItem(BaseModel):
    id: str
    name: str
    code: str
    description: str | None = None
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class TaxClassListResponse(BaseModel):
    items: list[TaxClassItem]
    total: int
    limit: int
    offset: int


class TaxRateCreateRequest(BaseModel):
    country: str = Field(..., min_length=2, max_length=2)
    state: str | None = Field(default=None, max_length=64)
    rate: float = Field(..., ge=0)
    tax_type: TaxType = TaxType.other
    is_inclusive: bool = False
    priority: int = 0
    is_active: bool = True


class TaxRateUpdateRequest(BaseModel):
    country: str | None = Field(default=None, min_length=2, max_length=2)
    state: str | None = None
    rate: float | None = Field(default=None, ge=0)
    tax_type: TaxType | None = None
    is_inclusive: bool | None = None
    priority: int | None = None
    is_active: bool | None = None


class TaxRateItem(BaseModel):
    id: str
    tax_class_id: str
    country: str
    state: str | None = None
    rate: float
    tax_type: TaxType
    is_inclusive: bool
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class TaxCalculationResponse(BaseModel):
    amount: float
    tax_amount: float
    total_amount: float
    rate: float
    is_inclusive: bool
    country: str
    state: str | None = None
