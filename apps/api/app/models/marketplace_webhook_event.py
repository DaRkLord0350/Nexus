from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class MarketplaceWebhookStatus(str, PyEnum):
    pending = "pending"
    processed = "processed"
    failed = "failed"


# Retry-with-backoff is driven by next_retry_at + retry_count rather than a
# real task queue (no Celery beat/worker is configured in this codebase --
# see MarketplaceWebhookService for the manual "retry now" endpoint that
# stands in for a scheduled retry worker).
class MarketplaceWebhookEvent(Base, TimestampMixin, TenantMixin):
    __tablename__ = "marketplace_webhook_events"

    marketplace_connector_id = Column(String(36), ForeignKey("marketplace_connectors.id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    payload = Column(Text, nullable=False)

    status = Column(Enum(MarketplaceWebhookStatus, native_enum=False), nullable=False, default=MarketplaceWebhookStatus.pending, index=True)
    retry_count = Column(Integer, nullable=False, default=0)
    next_retry_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)

    received_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
