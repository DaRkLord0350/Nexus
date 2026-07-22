from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class Inventory(Base, TimestampMixin, TenantMixin):
    __tablename__ = "inventory"

    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(String(36), ForeignKey("variants.id", ondelete="CASCADE"), nullable=True, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    bin_id = Column(String(36), ForeignKey("warehouse_bins.id", ondelete="SET NULL"), nullable=True, index=True)

    quantity_available = Column(Integer, nullable=False, default=0)
    quantity_reserved = Column(Integer, nullable=False, default=0)
    quantity_incoming = Column(Integer, nullable=False, default=0)
    quantity_damaged = Column(Integer, nullable=False, default=0)
    quantity_returned = Column(Integer, nullable=False, default=0)

    minimum_stock = Column(Integer, nullable=True)
    maximum_stock = Column(Integer, nullable=True)
    reorder_point = Column(Integer, nullable=True)
    average_cost = Column(Float, nullable=True)

    last_counted_at = Column(DateTime, nullable=True)
    low_stock_notified_at = Column(DateTime, nullable=True)
