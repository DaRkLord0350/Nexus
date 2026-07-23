from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class OrderStatus(str, PyEnum):
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


class OrderPriority(str, PyEnum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class PaymentStatus(str, PyEnum):
    pending = "pending"
    authorized = "authorized"
    paid = "paid"
    partially_paid = "partially_paid"
    refunded = "refunded"
    partially_refunded = "partially_refunded"
    failed = "failed"


class Order(Base, TimestampMixin, TenantMixin):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("organization_id", "order_number", name="uq_order_organization_number"),
    )

    order_number = Column(String(50), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    cart_id = Column(String(36), ForeignKey("carts.id", ondelete="SET NULL"), nullable=True, index=True)

    status = Column(Enum(OrderStatus, native_enum=False), nullable=False, default=OrderStatus.pending, index=True)
    previous_status = Column(Enum(OrderStatus, native_enum=False), nullable=True)
    priority = Column(Enum(OrderPriority, native_enum=False), nullable=False, default=OrderPriority.normal, index=True)

    currency = Column(String(3), nullable=False, default="USD")
    subtotal = Column(Float, nullable=False, default=0)
    discount_amount = Column(Float, nullable=False, default=0)
    tax_amount = Column(Float, nullable=False, default=0)
    shipping_amount = Column(Float, nullable=False, default=0)
    total = Column(Float, nullable=False, default=0)
    amount_paid = Column(Float, nullable=False, default=0)
    amount_refunded = Column(Float, nullable=False, default=0)

    coupon_id = Column(String(36), ForeignKey("coupons.id", ondelete="SET NULL"), nullable=True, index=True)
    coupon_code = Column(String(64), nullable=True)

    payment_method = Column(String(32), nullable=True)
    payment_status = Column(Enum(PaymentStatus, native_enum=False), nullable=False, default=PaymentStatus.pending, index=True)

    shipping_method = Column(String(128), nullable=True)

    billing_address_id = Column(String(36), ForeignKey("addresses.id", ondelete="SET NULL"), nullable=True)
    billing_first_name = Column(String(128), nullable=True)
    billing_last_name = Column(String(128), nullable=True)
    billing_company = Column(String(255), nullable=True)
    billing_phone = Column(String(50), nullable=True)
    billing_line1 = Column(String(255), nullable=True)
    billing_line2 = Column(String(255), nullable=True)
    billing_city = Column(String(128), nullable=True)
    billing_state = Column(String(128), nullable=True)
    billing_postal_code = Column(String(32), nullable=True)
    billing_country = Column(String(2), nullable=True)

    shipping_address_id = Column(String(36), ForeignKey("addresses.id", ondelete="SET NULL"), nullable=True)
    shipping_first_name = Column(String(128), nullable=True)
    shipping_last_name = Column(String(128), nullable=True)
    shipping_company = Column(String(255), nullable=True)
    shipping_phone = Column(String(50), nullable=True)
    shipping_line1 = Column(String(255), nullable=True)
    shipping_line2 = Column(String(255), nullable=True)
    shipping_city = Column(String(128), nullable=True)
    shipping_state = Column(String(128), nullable=True)
    shipping_postal_code = Column(String(32), nullable=True)
    shipping_country = Column(String(2), nullable=True)

    customer_note = Column(Text, nullable=True)
    gift_note = Column(Text, nullable=True)
    cancelled_reason = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)

    fraud_score = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    requires_manual_review = Column(Boolean, nullable=False, default=False)
    source = Column(String(32), nullable=False, default="web")

    placed_at = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    packed_at = Column(DateTime, nullable=True)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
