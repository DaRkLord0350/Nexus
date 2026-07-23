from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class ShippingLabelType(str, PyEnum):
    label = "label"
    packing_slip = "packing_slip"
    manifest = "manifest"
    return_label = "return_label"


class ShippingLabel(Base, TimestampMixin, TenantMixin):
    __tablename__ = "shipping_labels"

    shipment_id = Column(String(36), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True)
    label_type = Column(Enum(ShippingLabelType, native_enum=False), nullable=False, default=ShippingLabelType.label)
    format = Column(String(16), nullable=False, default="html")
    generated_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
