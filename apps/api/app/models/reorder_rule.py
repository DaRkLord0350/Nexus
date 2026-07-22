from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class ReorderRule(Base, TimestampMixin, TenantMixin):
    __tablename__ = "reorder_rules"

    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(String(36), ForeignKey("variants.id", ondelete="CASCADE"), nullable=True, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    minimum_stock = Column(Integer, nullable=False)
    maximum_stock = Column(Integer, nullable=True)
    reorder_quantity = Column(Integer, nullable=False)
    supplier_name = Column(String(255), nullable=True)
    lead_time_days = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    last_triggered_at = Column(DateTime, nullable=True)
