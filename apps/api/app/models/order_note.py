from sqlalchemy import Boolean, Column, ForeignKey, String, Text

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class OrderNote(Base, TimestampMixin, TenantMixin):
    __tablename__ = "order_notes"

    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    note = Column(Text, nullable=False)
    is_customer_visible = Column(Boolean, nullable=False, default=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
