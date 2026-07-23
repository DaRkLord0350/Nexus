from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class ReturnShipmentStatus(str, PyEnum):
    pending = "pending"
    label_generated = "label_generated"
    reverse_pickup_scheduled = "reverse_pickup_scheduled"
    in_transit = "in_transit"
    received = "received"
    cancelled = "cancelled"


class ReturnShipment(Base, TimestampMixin, TenantMixin):
    __tablename__ = "return_shipments"
    __table_args__ = (
        UniqueConstraint("organization_id", "return_shipment_number", name="uq_return_shipment_organization_number"),
    )

    return_shipment_number = Column(String(50), nullable=False, index=True)
    return_request_id = Column(String(36), ForeignKey("return_requests.id"), nullable=False, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=False, index=True)
    shipping_provider_id = Column(String(36), ForeignKey("shipping_providers.id", ondelete="SET NULL"), nullable=True, index=True)

    status = Column(Enum(ReturnShipmentStatus, native_enum=False), nullable=False, default=ReturnShipmentStatus.pending, index=True)
    tracking_number = Column(String(128), nullable=True, index=True)
    carrier_name = Column(String(128), nullable=True)

    pickup_contact_name = Column(String(128), nullable=True)
    pickup_contact_phone = Column(String(50), nullable=True)
    pickup_line1 = Column(String(255), nullable=True)
    pickup_city = Column(String(128), nullable=True)
    pickup_state = Column(String(128), nullable=True)
    pickup_postal_code = Column(String(32), nullable=True)
    pickup_country = Column(String(2), nullable=True)

    reverse_pickup_scheduled_at = Column(DateTime, nullable=True)
    reverse_pickup_completed_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    notes = Column(Text, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
