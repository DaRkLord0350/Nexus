from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, Enum, Float, ForeignKey, Integer, String, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class VariantStatus(str, PyEnum):
    active = "active"
    archived = "archived"


class Variant(Base, TimestampMixin, TenantMixin):
    __tablename__ = "variants"
    __table_args__ = (
        UniqueConstraint("organization_id", "sku", name="uq_variant_organization_sku"),
    )

    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(100), nullable=False, index=True)
    barcode = Column(String(100), nullable=True, index=True)
    weight = Column(Float, nullable=True)
    weight_unit = Column(String(16), nullable=True)
    status = Column(Enum(VariantStatus, native_enum=False), nullable=False, default=VariantStatus.active)
    is_default = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=0)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
