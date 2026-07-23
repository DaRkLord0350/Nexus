from pydantic import BaseModel, Field


class ShippingRateCreateRequest(BaseModel):
    shipping_provider_id: str
    name: str = Field(..., min_length=1, max_length=255)
    origin_country: str | None = Field(default=None, min_length=2, max_length=2)
    destination_country: str | None = Field(default=None, min_length=2, max_length=2)
    destination_state: str | None = None
    min_weight: float | None = Field(default=None, ge=0)
    max_weight: float | None = Field(default=None, ge=0)
    base_price: float = Field(default=0, ge=0)
    price_per_kg: float | None = Field(default=None, ge=0)
    cod_fee: float | None = Field(default=None, ge=0)
    insurance_fee: float | None = Field(default=None, ge=0)
    transit_days_min: int | None = Field(default=None, ge=0)
    transit_days_max: int | None = Field(default=None, ge=0)
    delivery_rating: float | None = Field(default=None, ge=0, le=5)
    is_active: bool = True


class ShippingRateUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    origin_country: str | None = Field(default=None, min_length=2, max_length=2)
    destination_country: str | None = Field(default=None, min_length=2, max_length=2)
    destination_state: str | None = None
    min_weight: float | None = Field(default=None, ge=0)
    max_weight: float | None = Field(default=None, ge=0)
    base_price: float | None = Field(default=None, ge=0)
    price_per_kg: float | None = Field(default=None, ge=0)
    cod_fee: float | None = Field(default=None, ge=0)
    insurance_fee: float | None = Field(default=None, ge=0)
    transit_days_min: int | None = Field(default=None, ge=0)
    transit_days_max: int | None = Field(default=None, ge=0)
    delivery_rating: float | None = Field(default=None, ge=0, le=5)
    is_active: bool | None = None


class ShippingRateRead(BaseModel):
    id: str
    shipping_provider_id: str
    name: str
    origin_country: str | None = None
    destination_country: str | None = None
    destination_state: str | None = None
    min_weight: float | None = None
    max_weight: float | None = None
    base_price: float
    price_per_kg: float | None = None
    cod_fee: float | None = None
    insurance_fee: float | None = None
    transit_days_min: int | None = None
    transit_days_max: int | None = None
    delivery_rating: float | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class ShippingRateListResponse(BaseModel):
    items: list[ShippingRateRead]
    total: int
    limit: int
    offset: int


class RateCompareRequest(BaseModel):
    destination_country: str = Field(..., min_length=2, max_length=2)
    destination_state: str | None = None
    weight: float = Field(default=0.5, ge=0)
    is_cod: bool = False
    needs_insurance: bool = False


class RateQuote(BaseModel):
    shipping_provider_id: str
    provider_name: str
    rate_id: str | None = None
    cost: float
    transit_days_min: int | None = None
    transit_days_max: int | None = None
    supports_cod: bool
    supports_insurance: bool
    delivery_rating: float | None = None
    recommended: bool = False
    score: float = 0.0


class RateCompareResponse(BaseModel):
    quotes: list[RateQuote]
