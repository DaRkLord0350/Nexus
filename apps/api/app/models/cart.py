from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String, Text

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class CartStatus(str, PyEnum):
    active = "active"
    merged = "merged"
    converted = "converted"
    abandoned = "abandoned"


class Cart(Base, TimestampMixin, TenantMixin):
    __tablename__ = "carts"

    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=True, index=True)
    session_token = Column(String(128), nullable=True, index=True)
    status = Column(Enum(CartStatus, native_enum=False), nullable=False, default=CartStatus.active, index=True)
    currency = Column(String(3), nullable=False, default="USD")
    coupon_id = Column(String(36), ForeignKey("coupons.id", ondelete="SET NULL"), nullable=True, index=True)
    coupon_code = Column(String(64), nullable=True)
    subtotal = Column(Float, nullable=False, default=0)
    discount_amount = Column(Float, nullable=False, default=0)
    tax_amount = Column(Float, nullable=False, default=0)
    shipping_amount = Column(Float, nullable=False, default=0)
    total = Column(Float, nullable=False, default=0)
    notes = Column(Text, nullable=True)
    order_id = Column(String(36), nullable=True, index=True)
    expires_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, nullable=True)
