from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class ShipmentStatus(str, PyEnum):
    pending = "pending"
    label_generated = "label_generated"
    picked_up = "picked_up"
    in_transit = "in_transit"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    failed_delivery = "failed_delivery"
    returned_to_origin = "returned_to_origin"
    cancelled = "cancelled"


class Shipment(Base, TimestampMixin, TenantMixin):
    __tablename__ = "shipments"
    __table_args__ = (
        UniqueConstraint("organization_id", "shipment_number", name="uq_shipment_organization_number"),
    )

    shipment_number = Column(String(50), nullable=False, index=True)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False, index=True)
    pickup_id = Column(String(36), ForeignKey("pickups.id", ondelete="SET NULL"), nullable=True, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=False, index=True)
    shipping_provider_id = Column(String(36), ForeignKey("shipping_providers.id", ondelete="SET NULL"), nullable=True, index=True)

    status = Column(Enum(ShipmentStatus, native_enum=False), nullable=False, default=ShipmentStatus.pending, index=True)
    tracking_number = Column(String(128), nullable=True, index=True)
    carrier_name = Column(String(128), nullable=True)
    service_type = Column(String(64), nullable=True)

    weight = Column(Float, nullable=True)
    length = Column(Float, nullable=True)
    width = Column(Float, nullable=True)
    height = Column(Float, nullable=True)

    shipping_cost = Column(Float, nullable=False, default=0)
    insurance_amount = Column(Float, nullable=True)
    is_cod = Column(Boolean, nullable=False, default=False)
    cod_amount = Column(Float, nullable=True)

    expected_delivery_date = Column(DateTime, nullable=True)
    picked_up_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    delivery_attempts = Column(Integer, nullable=False, default=0)

    notes = Column(Text, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
