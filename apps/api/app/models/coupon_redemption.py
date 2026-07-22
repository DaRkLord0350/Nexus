from sqlalchemy import Column, DateTime, ForeignKey, String
from datetime import datetime

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class CouponRedemption(Base, TimestampMixin, TenantMixin):
    __tablename__ = "coupon_redemptions"

    coupon_id = Column(String(36), ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    order_id = Column(String(36), nullable=True, index=True)
    redeemed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
