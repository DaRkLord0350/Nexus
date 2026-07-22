from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CouponDiscountType(str, Enum):
    percentage = "percentage"
    fixed_amount = "fixed_amount"
    free_shipping = "free_shipping"
    buy_x_get_y = "buy_x_get_y"


class CouponCreateRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=64)
    name: str | None = None
    description: str | None = None
    discount_type: CouponDiscountType = CouponDiscountType.percentage
    discount_value: float | None = Field(default=None, ge=0)
    buy_quantity: int | None = Field(default=None, ge=1)
    get_quantity: int | None = Field(default=None, ge=1)
    get_discount_percentage: float | None = Field(default=100.0, ge=0, le=100)
    min_order_amount: float | None = Field(default=None, ge=0)
    max_discount_amount: float | None = Field(default=None, ge=0)
    usage_limit: int | None = Field(default=None, ge=1)
    usage_limit_per_customer: int | None = Field(default=None, ge=1)
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool = True
    product_ids: list[str] = Field(default_factory=list)
    category_ids: list[str] = Field(default_factory=list)
    collection_ids: list[str] = Field(default_factory=list)


class CouponUpdateRequest(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = None
    description: str | None = None
    discount_type: CouponDiscountType | None = None
    discount_value: float | None = Field(default=None, ge=0)
    buy_quantity: int | None = Field(default=None, ge=1)
    get_quantity: int | None = Field(default=None, ge=1)
    get_discount_percentage: float | None = Field(default=None, ge=0, le=100)
    min_order_amount: float | None = None
    max_discount_amount: float | None = None
    usage_limit: int | None = None
    usage_limit_per_customer: int | None = None
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool | None = None
    product_ids: list[str] | None = None
    category_ids: list[str] | None = None
    collection_ids: list[str] | None = None


class CouponItem(BaseModel):
    id: str
    code: str
    name: str | None = None
    description: str | None = None
    discount_type: CouponDiscountType
    discount_value: float | None = None
    buy_quantity: int | None = None
    get_quantity: int | None = None
    get_discount_percentage: float | None = None
    min_order_amount: float | None = None
    max_discount_amount: float | None = None
    usage_limit: int | None = None
    usage_limit_per_customer: int | None = None
    used_count: int
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool
    product_ids: list[str] = Field(default_factory=list)
    category_ids: list[str] = Field(default_factory=list)
    collection_ids: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class CouponListResponse(BaseModel):
    items: list[CouponItem]
    total: int
    limit: int
    offset: int


class CouponValidateRequest(BaseModel):
    code: str
    order_amount: float = Field(..., ge=0)
    product_ids: list[str] = Field(default_factory=list)
    category_ids: list[str] = Field(default_factory=list)
    collection_ids: list[str] = Field(default_factory=list)
    quantity: int = Field(default=1, ge=1)
    unit_price: float = Field(default=0, ge=0)
    customer_id: str | None = None


class CouponValidationResponse(BaseModel):
    valid: bool
    reason: str | None = None
    discount_amount: float = 0
    free_shipping: bool = False
    coupon_id: str | None = None


class CouponRedeemRequest(BaseModel):
    customer_id: str | None = None
    order_id: str | None = None


class BulkDeleteRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1)
