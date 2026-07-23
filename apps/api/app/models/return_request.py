from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class ReturnStatus(str, PyEnum):
    requested = "requested"
    approved = "approved"
    rejected = "rejected"
    awaiting_pickup = "awaiting_pickup"
    in_transit = "in_transit"
    received = "received"
    inspecting = "inspecting"
    completed = "completed"
    cancelled = "cancelled"


class ReturnResolution(str, PyEnum):
    refund = "refund"
    replacement = "replacement"
    exchange = "exchange"
    repair = "repair"
    store_credit = "store_credit"


class ReturnRequest(Base, TimestampMixin, TenantMixin):
    __tablename__ = "return_requests"
    __table_args__ = (
        UniqueConstraint("organization_id", "return_number", name="uq_return_request_organization_number"),
    )

    return_number = Column(String(50), nullable=False, index=True)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=True, index=True)

    status = Column(Enum(ReturnStatus, native_enum=False), nullable=False, default=ReturnStatus.requested, index=True)
    resolution = Column(Enum(ReturnResolution, native_enum=False), nullable=True)

    reason_code = Column(String(64), nullable=False)
    reason_notes = Column(Text, nullable=True)

    inspection_notes = Column(Text, nullable=True)
    inspected_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    inspected_at = Column(DateTime, nullable=True)

    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_reason = Column(Text, nullable=True)

    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
