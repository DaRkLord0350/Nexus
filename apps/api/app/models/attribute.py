from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class AttributeInputType(str, PyEnum):
    select = "select"
    text = "text"
    number = "number"
    boolean = "boolean"


class Attribute(Base, TimestampMixin, TenantMixin):
    __tablename__ = "attributes"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_attribute_organization_code"),
    )

    name = Column(String(255), nullable=False)
    code = Column(String(255), nullable=False, index=True)
    input_type = Column(Enum(AttributeInputType, native_enum=False), nullable=False, default=AttributeInputType.select)
    is_variant_attribute = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    values = relationship("AttributeValue", viewonly=True)
