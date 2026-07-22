from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class ProductTypeAttribute(Base, TimestampMixin, TenantMixin):
    __tablename__ = "product_type_attributes"
    __table_args__ = (
        UniqueConstraint("product_type_id", "attribute_id", name="uq_product_type_attribute"),
    )

    product_type_id = Column(String(36), ForeignKey("product_types.id", ondelete="CASCADE"), nullable=False, index=True)
    attribute_id = Column(String(36), ForeignKey("attributes.id", ondelete="CASCADE"), nullable=False, index=True)
    is_required = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=0)
