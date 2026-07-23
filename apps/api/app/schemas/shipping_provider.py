from datetime import datetime

from pydantic import BaseModel, Field


class ShippingProviderCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=64)
    provider_type: str = Field(default="manual", max_length=32)
    is_active: bool = True
    is_default: bool = False
    priority: int = 0
    credentials: dict | None = None
    webhook_secret: str | None = None
    supports_cod: bool = True
    supports_insurance: bool = False
    supports_reverse_pickup: bool = False
    supports_international: bool = False
    base_rate: float | None = Field(default=None, ge=0)
    base_transit_days: int | None = Field(default=None, ge=0)


class ShippingProviderUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    provider_type: str | None = Field(default=None, max_length=32)
    is_active: bool | None = None
    is_default: bool | None = None
    priority: int | None = None
    credentials: dict | None = None
    webhook_secret: str | None = None
    supports_cod: bool | None = None
    supports_insurance: bool | None = None
    supports_reverse_pickup: bool | None = None
    supports_international: bool | None = None
    base_rate: float | None = Field(default=None, ge=0)
    base_transit_days: int | None = Field(default=None, ge=0)


class ShippingProviderRead(BaseModel):
    id: str
    name: str
    code: str
    provider_type: str
    is_active: bool
    is_default: bool
    priority: int
    supports_cod: bool
    supports_insurance: bool
    supports_reverse_pickup: bool
    supports_international: bool
    base_rate: float | None = None
    base_transit_days: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShippingProviderListResponse(BaseModel):
    items: list[ShippingProviderRead]
    total: int
    limit: int
    offset: int
