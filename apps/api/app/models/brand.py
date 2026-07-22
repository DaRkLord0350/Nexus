from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class BrandStatus(str, PyEnum):
    draft = "draft"
    active = "active"
    archived = "archived"


class Brand(Base, TimestampMixin, TenantMixin):
    __tablename__ = "brands"
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_brand_organization_slug"),
    )

    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String(1024), nullable=True)
    website = Column(String(1024), nullable=True)
    is_featured = Column(Boolean, nullable=False, default=False)
    status = Column(Enum(BrandStatus, native_enum=False), nullable=False, default=BrandStatus.active)
    seo_title = Column(String(255), nullable=True)
    seo_description = Column(String(500), nullable=True)
    seo_keywords = Column(String(500), nullable=True)
    og_image_url = Column(String(1024), nullable=True)
    canonical_url = Column(String(1024), nullable=True)
    no_index = Column(Boolean, nullable=False, default=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
