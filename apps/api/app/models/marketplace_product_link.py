from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class MarketplaceLinkStatus(str, PyEnum):
    pending = "pending"
    synced = "synced"
    failed = "failed"


class MarketplaceProductLink(Base, TimestampMixin, TenantMixin):
    __tablename__ = "marketplace_product_links"
    __table_args__ = (
        UniqueConstraint("marketplace_connector_id", "product_id", name="uq_marketplace_product_link_connector_product"),
    )

    marketplace_connector_id = Column(String(36), ForeignKey("marketplace_connectors.id"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)

    external_id = Column(String(255), nullable=True, index=True)
    external_sku = Column(String(100), nullable=True)
    external_url = Column(String(500), nullable=True)

    sync_status = Column(Enum(MarketplaceLinkStatus, native_enum=False), nullable=False, default=MarketplaceLinkStatus.pending, index=True)
    last_synced_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    last_synced_price = Column(Float, nullable=True)
    last_synced_quantity = Column(Integer, nullable=True)
