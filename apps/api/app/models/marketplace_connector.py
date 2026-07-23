from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin

# Recognized connector_type values (kept as a free-text column, not a native
# enum, so new marketplaces can be added without a migration -- mirrors the
# ShippingProvider.provider_type convention):
# woocommerce, amazon, flipkart, shopify, etsy, ebay, other


class MarketplaceConnector(Base, TimestampMixin, TenantMixin):
    __tablename__ = "marketplace_connectors"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_marketplace_connector_organization_code"),
    )

    name = Column(String(255), nullable=False)
    code = Column(String(64), nullable=False, index=True)
    connector_type = Column(String(32), nullable=False, default="other", index=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Credentials are stored as a JSON-encoded string, same documented gap as
    # ShippingProvider.credentials: this should be encrypted at rest in
    # production (KMS-backed field encryption or a secrets-manager
    # reference), but no such utility exists in this codebase yet.
    credentials = Column(Text, nullable=True)
    webhook_secret = Column(String(255), nullable=True)
    store_url = Column(String(500), nullable=True)

    auto_sync_products = Column(Boolean, nullable=False, default=False)
    auto_sync_orders = Column(Boolean, nullable=False, default=False)
    auto_sync_inventory = Column(Boolean, nullable=False, default=False)
    auto_sync_prices = Column(Boolean, nullable=False, default=False)
    sync_interval_minutes = Column(Integer, nullable=False, default=60)

    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(String(16), nullable=True)

    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
