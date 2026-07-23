from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin

# Recognized provider_type values (kept as a free-text column, not a native
# enum, so new couriers can be added without a migration):
# shiprocket, delhivery, bluedart, fedex, dhl, aramex, ups, manual, other


class ShippingProvider(Base, TimestampMixin, TenantMixin):
    __tablename__ = "shipping_providers"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_shipping_provider_organization_code"),
    )

    name = Column(String(255), nullable=False)
    code = Column(String(64), nullable=False, index=True)
    provider_type = Column(String(32), nullable=False, default="manual", index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    is_default = Column(Boolean, nullable=False, default=False)
    priority = Column(Integer, nullable=False, default=0)

    # Credentials are stored as a JSON-encoded string. In production this
    # column should be encrypted at rest (e.g. via a KMS-backed field
    # encryption layer or by keeping only a reference here and the real
    # secret in AWS Secrets Manager) -- no such field-encryption utility
    # exists in this codebase yet, so this is a documented gap rather than a
    # silently-fake protection.
    credentials = Column(Text, nullable=True)
    webhook_secret = Column(String(255), nullable=True)

    supports_cod = Column(Boolean, nullable=False, default=True)
    supports_insurance = Column(Boolean, nullable=False, default=False)
    supports_reverse_pickup = Column(Boolean, nullable=False, default=False)
    supports_international = Column(Boolean, nullable=False, default=False)

    base_rate = Column(Float, nullable=True)
    base_transit_days = Column(Integer, nullable=True)

    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
