from sqlalchemy import Column, ForeignKey, String, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class VariantAttributeValue(Base, TimestampMixin, TenantMixin):
    __tablename__ = "variant_attribute_values"
    __table_args__ = (
        UniqueConstraint("variant_id", "attribute_value_id", name="uq_variant_attribute_value"),
    )

    variant_id = Column(String(36), ForeignKey("variants.id", ondelete="CASCADE"), nullable=False, index=True)
    attribute_value_id = Column(String(36), ForeignKey("attribute_values.id", ondelete="CASCADE"), nullable=False, index=True)
