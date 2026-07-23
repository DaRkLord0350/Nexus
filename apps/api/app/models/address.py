from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, String

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class AddressType(str, PyEnum):
    billing = "billing"
    shipping = "shipping"
    both = "both"


class Address(Base, TimestampMixin, TenantMixin):
    __tablename__ = "addresses"

    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(64), nullable=True)
    address_type = Column(Enum(AddressType, native_enum=False), nullable=False, default=AddressType.shipping)
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    company = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    line1 = Column(String(255), nullable=False)
    line2 = Column(String(255), nullable=True)
    city = Column(String(128), nullable=False)
    state = Column(String(128), nullable=True)
    postal_code = Column(String(32), nullable=True)
    country = Column(String(2), nullable=False)
    is_default = Column(Boolean, nullable=False, default=False)
