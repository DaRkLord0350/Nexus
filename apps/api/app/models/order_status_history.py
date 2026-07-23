from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class OrderStatusHistory(Base, TimestampMixin, TenantMixin):
    __tablename__ = "order_status_history"

    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = Column(String(32), nullable=True)
    to_status = Column(String(32), nullable=False)
    notes = Column(Text, nullable=True)
    changed_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    changed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
