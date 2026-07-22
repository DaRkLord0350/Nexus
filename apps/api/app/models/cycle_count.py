from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class CycleCountStatus(str, PyEnum):
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class CycleCount(Base, TimestampMixin, TenantMixin):
    __tablename__ = "cycle_counts"
    __table_args__ = (
        UniqueConstraint("organization_id", "count_number", name="uq_cycle_count_organization_number"),
    )

    count_number = Column(String(50), nullable=False, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    zone_id = Column(String(36), ForeignKey("warehouse_zones.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(Enum(CycleCountStatus, native_enum=False), nullable=False, default=CycleCountStatus.scheduled, index=True)
    scheduled_date = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    assigned_to = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    notes = Column(Text, nullable=True)
