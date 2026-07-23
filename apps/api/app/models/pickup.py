from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class PickupStatus(str, PyEnum):
    scheduled = "scheduled"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"
    missed = "missed"


class Pickup(Base, TimestampMixin, TenantMixin):
    __tablename__ = "pickups"
    __table_args__ = (
        UniqueConstraint("organization_id", "pickup_number", name="uq_pickup_organization_number"),
    )

    pickup_number = Column(String(50), nullable=False, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=False, index=True)
    shipping_provider_id = Column(String(36), ForeignKey("shipping_providers.id", ondelete="SET NULL"), nullable=True, index=True)

    status = Column(Enum(PickupStatus, native_enum=False), nullable=False, default=PickupStatus.scheduled, index=True)
    scheduled_date = Column(DateTime, nullable=False)
    time_slot = Column(String(64), nullable=True)
    contact_name = Column(String(128), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancelled_reason = Column(Text, nullable=True)

    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
