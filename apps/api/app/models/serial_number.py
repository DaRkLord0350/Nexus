from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class SerialStatus(str, PyEnum):
    available = "available"
    reserved = "reserved"
    sold = "sold"
    returned = "returned"
    damaged = "damaged"


class SerialNumber(Base, TimestampMixin, TenantMixin):
    __tablename__ = "serial_numbers"
    __table_args__ = (
        UniqueConstraint("organization_id", "product_id", "serial", name="uq_serial_organization_product_serial"),
    )

    inventory_id = Column(String(36), ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(String(36), ForeignKey("variants.id", ondelete="CASCADE"), nullable=True, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id = Column(String(36), ForeignKey("batches.id", ondelete="SET NULL"), nullable=True, index=True)
    bin_id = Column(String(36), ForeignKey("warehouse_bins.id", ondelete="SET NULL"), nullable=True, index=True)

    serial = Column(String(150), nullable=False, index=True)
    status = Column(Enum(SerialStatus, native_enum=False), nullable=False, default=SerialStatus.available, index=True)
    sold_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
