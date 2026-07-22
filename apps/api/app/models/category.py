from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class CategoryStatus(str, PyEnum):
    draft = "draft"
    active = "active"
    archived = "archived"


class Category(Base, TimestampMixin, TenantMixin):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_category_organization_slug"),
    )

    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(String(36), ForeignKey("categories.id"), nullable=True, index=True)
    path = Column(String(1024), nullable=False, index=True)
    image_url = Column(String(1024), nullable=True)
    banner_url = Column(String(1024), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_featured = Column(Boolean, nullable=False, default=False)
    is_visible = Column(Boolean, nullable=False, default=True)
    status = Column(Enum(CategoryStatus, native_enum=False), nullable=False, default=CategoryStatus.active)
    seo_title = Column(String(255), nullable=True)
    seo_description = Column(String(500), nullable=True)
    seo_keywords = Column(String(500), nullable=True)
    og_image_url = Column(String(1024), nullable=True)
    canonical_url = Column(String(1024), nullable=True)
    no_index = Column(Boolean, nullable=False, default=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)


Category.parent = relationship("Category", remote_side=[Category.id], backref="children")
