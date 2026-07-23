from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class MarketplaceOrderLinkStatus(str, PyEnum):
    imported = "imported"
    failed = "failed"
    ignored = "ignored"


class MarketplaceOrderLink(Base, TimestampMixin, TenantMixin):
    __tablename__ = "marketplace_order_links"
    __table_args__ = (
        UniqueConstraint("marketplace_connector_id", "external_order_id", name="uq_marketplace_order_link_connector_external_id"),
    )

    marketplace_connector_id = Column(String(36), ForeignKey("marketplace_connectors.id"), nullable=False, index=True)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=True, index=True)

    external_order_id = Column(String(255), nullable=False, index=True)
    external_order_number = Column(String(100), nullable=True)
    raw_payload = Column(Text, nullable=True)

    status = Column(Enum(MarketplaceOrderLinkStatus, native_enum=False), nullable=False, default=MarketplaceOrderLinkStatus.imported, index=True)
    last_error = Column(Text, nullable=True)
    imported_at = Column(DateTime, nullable=True)
