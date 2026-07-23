from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class MarketplaceSyncType(str, PyEnum):
    product = "product"
    order = "order"
    inventory = "inventory"
    price = "price"


class MarketplaceSyncStatus(str, PyEnum):
    success = "success"
    partial = "partial"
    failed = "failed"


class MarketplaceSyncLog(Base, TimestampMixin, TenantMixin):
    __tablename__ = "marketplace_sync_logs"

    marketplace_connector_id = Column(String(36), ForeignKey("marketplace_connectors.id"), nullable=False, index=True)
    sync_type = Column(Enum(MarketplaceSyncType, native_enum=False), nullable=False, index=True)
    status = Column(Enum(MarketplaceSyncStatus, native_enum=False), nullable=False, index=True)
    triggered_by = Column(String(16), nullable=False, default="manual")

    items_processed = Column(Integer, nullable=False, default=0)
    items_succeeded = Column(Integer, nullable=False, default=0)
    items_failed = Column(Integer, nullable=False, default=0)

    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
