from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    draft = "draft"
    pending = "pending"
    confirmed = "confirmed"
    processing = "processing"
    packed = "packed"
    ready_to_ship = "ready_to_ship"
    shipped = "shipped"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    cancelled = "cancelled"
    failed = "failed"
    hold = "hold"
    partially_fulfilled = "partially_fulfilled"
    backordered = "backordered"


class OrderPriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class PaymentStatus(str, Enum):
    pending = "pending"
    authorized = "authorized"
    paid = "paid"
    partially_paid = "partially_paid"
    refunded = "refunded"
    partially_refunded = "partially_refunded"
    failed = "failed"


class OrderAddressInput(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=128)
    last_name: str = Field(..., min_length=1, max_length=128)
    company: str | None = None
    phone: str | None = None
    line1: str = Field(..., min_length=1, max_length=255)
    line2: str | None = None
    city: str = Field(..., min_length=1, max_length=128)
    state: str | None = None
    postal_code: str | None = None
    country: str = Field(..., min_length=2, max_length=2)


class OrderLineItemInput(BaseModel):
    product_id: str
    variant_id: str | None = None
    warehouse_id: str | None = None
    quantity: int = Field(..., gt=0)
    unit_price: float | None = Field(default=None, ge=0)
    discount_amount: float = Field(default=0, ge=0)
    tax_amount: float = Field(default=0, ge=0)
    gift_note: str | None = None


class OrderCreateRequest(BaseModel):
    customer_id: str
    cart_id: str | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    billing_address: OrderAddressInput
    shipping_address: OrderAddressInput
    payment_method: str | None = None
    shipping_method: str | None = None
    shipping_amount: float = Field(default=0, ge=0)
    customer_note: str | None = None
    gift_note: str | None = None
    priority: OrderPriority = OrderPriority.normal
    source: str = Field(default="web", max_length=32)
    tags: str | None = None
    coupon_code: str | None = None
    items: list[OrderLineItemInput] = Field(default_factory=list)


class OrderUpdateRequest(BaseModel):
    priority: OrderPriority | None = None
    tags: str | None = None
    shipping_method: str | None = None
    customer_note: str | None = None
    gift_note: str | None = None
    fraud_score: float | None = Field(default=None, ge=0, le=100)
    risk_score: float | None = Field(default=None, ge=0, le=100)
    requires_manual_review: bool | None = None


class OrderCancelRequest(BaseModel):
    reason: str | None = None


class OrderHoldRequest(BaseModel):
    reason: str | None = None


class OrderLineItem(BaseModel):
    id: str
    order_id: str
    product_id: str
    variant_id: str | None = None
    warehouse_id: str | None = None
    sku: str
    product_name: str
    quantity: int
    quantity_fulfilled: int
    quantity_returned: int
    unit_price: float
    discount_amount: float
    tax_amount: float
    total: float
    gift_note: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderStatusHistoryRead(BaseModel):
    id: str
    order_id: str
    from_status: str | None = None
    to_status: str
    notes: str | None = None
    changed_by: str | None = None
    changed_at: datetime

    model_config = {"from_attributes": True}


class OrderNoteCreateRequest(BaseModel):
    note: str = Field(..., min_length=1)
    is_customer_visible: bool = False


class OrderNoteRead(BaseModel):
    id: str
    order_id: str
    note: str
    is_customer_visible: bool
    created_by: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderRead(BaseModel):
    id: str
    order_number: str
    customer_id: str
    cart_id: str | None = None
    status: OrderStatus
    previous_status: OrderStatus | None = None
    priority: OrderPriority
    currency: str
    subtotal: float
    discount_amount: float
    tax_amount: float
    shipping_amount: float
    total: float
    amount_paid: float
    amount_refunded: float
    coupon_id: str | None = None
    coupon_code: str | None = None
    payment_method: str | None = None
    payment_status: PaymentStatus
    shipping_method: str | None = None
    billing_first_name: str | None = None
    billing_last_name: str | None = None
    billing_company: str | None = None
    billing_phone: str | None = None
    billing_line1: str | None = None
    billing_line2: str | None = None
    billing_city: str | None = None
    billing_state: str | None = None
    billing_postal_code: str | None = None
    billing_country: str | None = None
    shipping_first_name: str | None = None
    shipping_last_name: str | None = None
    shipping_company: str | None = None
    shipping_phone: str | None = None
    shipping_line1: str | None = None
    shipping_line2: str | None = None
    shipping_city: str | None = None
    shipping_state: str | None = None
    shipping_postal_code: str | None = None
    shipping_country: str | None = None
    customer_note: str | None = None
    gift_note: str | None = None
    cancelled_reason: str | None = None
    tags: str | None = None
    fraud_score: float | None = None
    risk_score: float | None = None
    requires_manual_review: bool
    source: str
    placed_at: datetime | None = None
    confirmed_at: datetime | None = None
    packed_at: datetime | None = None
    shipped_at: datetime | None = None
    delivered_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderDetail(OrderRead):
    items: list[OrderLineItem] = Field(default_factory=list)
    status_history: list[OrderStatusHistoryRead] = Field(default_factory=list)
    notes: list[OrderNoteRead] = Field(default_factory=list)


class OrderListResponse(BaseModel):
    items: list[OrderRead]
    total: int
    limit: int
    offset: int


class BulkPriorityUpdateRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1)
    priority: OrderPriority


class BulkTagRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1)
    tags: str
