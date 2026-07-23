from sqlalchemy import Column, Float, ForeignKey, Integer, String

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class RefundItem(Base, TimestampMixin, TenantMixin):
    __tablename__ = "refund_items"

    refund_id = Column(String(36), ForeignKey("refunds.id", ondelete="CASCADE"), nullable=False, index=True)
    order_item_id = Column(String(36), ForeignKey("order_items.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=True)
    amount = Column(Float, nullable=False)
