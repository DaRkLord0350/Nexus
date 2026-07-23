from pydantic import BaseModel, EmailStr, Field

from app.schemas.order import OrderAddressInput


class CheckoutRequest(BaseModel):
    cart_id: str
    session_token: str | None = None
    guest_email: EmailStr | None = None
    guest_first_name: str | None = None
    guest_last_name: str | None = None
    billing_address_id: str | None = None
    billing_address: OrderAddressInput | None = None
    shipping_address_id: str | None = None
    shipping_address: OrderAddressInput | None = None
    save_addresses: bool = False
    payment_method: str = Field(default="cod", max_length=32)
    shipping_method: str = Field(default="standard", max_length=128)
    customer_note: str | None = None
    gift_note: str | None = None


class CheckoutQuoteRequest(BaseModel):
    cart_id: str
    session_token: str | None = None
    country: str = Field(..., min_length=2, max_length=2)
    state: str | None = None
    shipping_method: str = Field(default="standard", max_length=128)


class CheckoutQuoteResponse(BaseModel):
    currency: str
    subtotal: float
    discount_amount: float
    tax_amount: float
    shipping_amount: float
    total: float
