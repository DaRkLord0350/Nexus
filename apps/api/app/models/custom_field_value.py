from sqlalchemy import Column, ForeignKey, JSON, String, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class CustomFieldValue(Base, TimestampMixin, TenantMixin):
    __tablename__ = "custom_field_values"
    __table_args__ = (
        UniqueConstraint("definition_id", "entity_id", name="uq_custom_field_value_definition_entity"),
    )

    definition_id = Column(String(36), ForeignKey("custom_field_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(32), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    value = Column(JSON, nullable=True)
