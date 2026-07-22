from enum import Enum as PyEnum

from sqlalchemy import Column, Enum, ForeignKey, Integer, String, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class WarehouseBinStatus(str, PyEnum):
    active = "active"
    full = "full"
    blocked = "blocked"
    inactive = "inactive"


class WarehouseBin(Base, TimestampMixin, TenantMixin):
    __tablename__ = "warehouse_bins"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "code", name="uq_warehouse_bin_warehouse_code"),
    )

    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    zone_id = Column(String(36), ForeignKey("warehouse_zones.id", ondelete="SET NULL"), nullable=True, index=True)
    code = Column(String(50), nullable=False, index=True)
    aisle = Column(String(50), nullable=True)
    rack = Column(String(50), nullable=True)
    shelf = Column(String(50), nullable=True)
    bin_number = Column(String(50), nullable=True)
    capacity = Column(Integer, nullable=True)
    status = Column(Enum(WarehouseBinStatus, native_enum=False), nullable=False, default=WarehouseBinStatus.active)
