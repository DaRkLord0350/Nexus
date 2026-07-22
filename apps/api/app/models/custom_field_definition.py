from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, JSON, String, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class CustomFieldEntityType(str, PyEnum):
    product = "product"
    variant = "variant"
    category = "category"
    brand = "brand"
    collection = "collection"


class CustomFieldType(str, PyEnum):
    text = "text"
    number = "number"
    boolean = "boolean"
    date = "date"
    select = "select"
    json = "json"


class CustomFieldDefinition(Base, TimestampMixin, TenantMixin):
    __tablename__ = "custom_field_definitions"
    __table_args__ = (
        UniqueConstraint("organization_id", "entity_type", "key", name="uq_custom_field_definition_org_entity_key"),
    )

    entity_type = Column(Enum(CustomFieldEntityType, native_enum=False), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    key = Column(String(100), nullable=False, index=True)
    field_type = Column(Enum(CustomFieldType, native_enum=False), nullable=False, default=CustomFieldType.text)
    options = Column(JSON, nullable=True)
    is_required = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
