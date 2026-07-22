from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class BatchStatus(str, PyEnum):
    active = "active"
    depleted = "depleted"
    expired = "expired"
    quarantined = "quarantined"
    recalled = "recalled"


class Batch(Base, TimestampMixin, TenantMixin):
    __tablename__ = "batches"
    __table_args__ = (
        UniqueConstraint("organization_id", "product_id", "warehouse_id", "batch_number", name="uq_batch_organization_product_warehouse_number"),
    )

    inventory_id = Column(String(36), ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(String(36), ForeignKey("variants.id", ondelete="CASCADE"), nullable=True, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)

    batch_number = Column(String(100), nullable=False, index=True)
    manufactured_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True, index=True)
    received_quantity = Column(Integer, nullable=False, default=0)
    remaining_quantity = Column(Integer, nullable=False, default=0)
    status = Column(Enum(BatchStatus, native_enum=False), nullable=False, default=BatchStatus.active, index=True)
    cost_price = Column(Float, nullable=True)
