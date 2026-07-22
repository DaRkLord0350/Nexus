from enum import Enum as PyEnum

from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class StockAdjustmentReason(str, PyEnum):
    damage = "damage"
    lost = "lost"
    found = "found"
    audit = "audit"
    manual = "manual"


class StockAdjustment(Base, TimestampMixin, TenantMixin):
    __tablename__ = "stock_adjustments"
    __table_args__ = (
        UniqueConstraint("organization_id", "adjustment_number", name="uq_stock_adjustment_organization_number"),
    )

    adjustment_number = Column(String(50), nullable=False, index=True)
    inventory_id = Column(String(36), ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(String(36), ForeignKey("variants.id", ondelete="CASCADE"), nullable=True, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    bin_id = Column(String(36), ForeignKey("warehouse_bins.id", ondelete="SET NULL"), nullable=True, index=True)
    quantity_delta = Column(Integer, nullable=False)
    reason = Column(Enum(StockAdjustmentReason, native_enum=False), nullable=False, default=StockAdjustmentReason.manual, index=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
