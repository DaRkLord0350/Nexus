from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CartStatus(str, Enum):
    active = "active"
    merged = "merged"
    converted = "converted"
    abandoned = "abandoned"


class CartGetOrCreateRequest(BaseModel):
    session_token: str | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)


class CartItemAddRequest(BaseModel):
    product_id: str
    variant_id: str | None = None
    quantity: int = Field(default=1, gt=0)
    gift_note: str | None = None


class CartItemUpdateRequest(BaseModel):
    quantity: int | None = Field(default=None, gt=0)
    saved_for_later: bool | None = None
    gift_note: str | None = None


class CartCouponRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=64)


class CartMergeRequest(BaseModel):
    session_token: str = Field(..., min_length=1)


class CartItemRead(BaseModel):
    id: str
    cart_id: str
    product_id: str
    variant_id: str | None = None
    quantity: int
    unit_price: float
    saved_for_later: bool
    gift_note: str | None = None
    line_total: float = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CartRead(BaseModel):
    id: str
    customer_id: str | None = None
    session_token: str | None = None
    status: CartStatus
    currency: str
    coupon_id: str | None = None
    coupon_code: str | None = None
    subtotal: float
    discount_amount: float
    tax_amount: float
    shipping_amount: float
    total: float
    notes: str | None = None
    order_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CartDetail(CartRead):
    items: list[CartItemRead] = Field(default_factory=list)
