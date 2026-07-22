from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class CycleCountItem(Base, TimestampMixin, TenantMixin):
    __tablename__ = "cycle_count_items"

    cycle_count_id = Column(String(36), ForeignKey("cycle_counts.id", ondelete="CASCADE"), nullable=False, index=True)
    inventory_id = Column(String(36), ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(String(36), ForeignKey("variants.id", ondelete="CASCADE"), nullable=True, index=True)
    bin_id = Column(String(36), ForeignKey("warehouse_bins.id", ondelete="SET NULL"), nullable=True, index=True)
    expected_quantity = Column(Integer, nullable=False)
    actual_quantity = Column(Integer, nullable=True)
    variance = Column(Integer, nullable=True)
    counted_at = Column(DateTime, nullable=True)
    counted_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    notes = Column(String(500), nullable=True)
