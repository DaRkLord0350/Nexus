from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, Enum, Float, ForeignKey, Integer, String

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class TaxType(str, PyEnum):
    gst = "gst"
    vat = "vat"
    sales_tax = "sales_tax"
    other = "other"


class TaxRate(Base, TimestampMixin, TenantMixin):
    __tablename__ = "tax_rates"

    tax_class_id = Column(String(36), ForeignKey("tax_classes.id", ondelete="CASCADE"), nullable=False, index=True)
    country = Column(String(2), nullable=False, index=True)
    state = Column(String(64), nullable=True, index=True)
    rate = Column(Float, nullable=False)
    tax_type = Column(Enum(TaxType, native_enum=False), nullable=False, default=TaxType.other)
    is_inclusive = Column(Boolean, nullable=False, default=False)
    priority = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
