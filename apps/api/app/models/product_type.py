from sqlalchemy import Boolean, Column, ForeignKey, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class ProductType(Base, TimestampMixin, TenantMixin):
    __tablename__ = "product_types"
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_product_type_organization_slug"),
    )

    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
