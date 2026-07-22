from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class WarehouseZoneType(str, PyEnum):
    receiving = "receiving"
    storage = "storage"
    picking = "picking"
    packing = "packing"
    returns = "returns"
    damaged = "damaged"


class WarehouseZone(Base, TimestampMixin, TenantMixin):
    __tablename__ = "warehouse_zones"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "code", name="uq_warehouse_zone_warehouse_code"),
    )

    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False, index=True)
    zone_type = Column(Enum(WarehouseZoneType, native_enum=False), nullable=False, default=WarehouseZoneType.storage)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
