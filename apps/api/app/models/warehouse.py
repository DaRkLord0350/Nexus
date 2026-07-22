from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class WarehouseType(str, PyEnum):
    main = "main"
    retail = "retail"
    returns = "returns"
    third_party = "third_party"


class Warehouse(Base, TimestampMixin, TenantMixin):
    __tablename__ = "warehouses"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_warehouse_organization_code"),
    )

    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False, index=True)
    warehouse_type = Column(Enum(WarehouseType, native_enum=False), nullable=False, default=WarehouseType.main)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    country = Column(String(128), nullable=True)
    state = Column(String(128), nullable=True)
    city = Column(String(128), nullable=True)
    zipcode = Column(String(32), nullable=True)
    address = Column(Text, nullable=True)
    is_default = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
