from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class CouponDiscountType(str, PyEnum):
    percentage = "percentage"
    fixed_amount = "fixed_amount"
    free_shipping = "free_shipping"
    buy_x_get_y = "buy_x_get_y"


class Coupon(Base, TimestampMixin, TenantMixin):
    __tablename__ = "coupons"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_coupon_organization_code"),
    )

    code = Column(String(64), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    discount_type = Column(Enum(CouponDiscountType, native_enum=False), nullable=False, default=CouponDiscountType.percentage)
    discount_value = Column(Float, nullable=True)
    buy_quantity = Column(Integer, nullable=True)
    get_quantity = Column(Integer, nullable=True)
    get_discount_percentage = Column(Float, nullable=True, default=100.0)
    min_order_amount = Column(Float, nullable=True)
    max_discount_amount = Column(Float, nullable=True)
    usage_limit = Column(Integer, nullable=True)
    usage_limit_per_customer = Column(Integer, nullable=True)
    used_count = Column(Integer, nullable=False, default=0)
    starts_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    expired_notified_at = Column(DateTime, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
