from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class AttributeValue(Base, TimestampMixin, TenantMixin):
    __tablename__ = "attribute_values"
    __table_args__ = (
        UniqueConstraint("attribute_id", "slug", name="uq_attribute_value_attribute_slug"),
    )

    attribute_id = Column(String(36), ForeignKey("attributes.id", ondelete="CASCADE"), nullable=False, index=True)
    value = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    color_hex = Column(String(16), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
