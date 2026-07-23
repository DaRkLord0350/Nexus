from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class ShipmentTracking(Base, TimestampMixin, TenantMixin):
    __tablename__ = "shipment_tracking_events"

    shipment_id = Column(String(36), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(32), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    occurred_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    source = Column(String(32), nullable=False, default="manual")
    raw_payload = Column(Text, nullable=True)
