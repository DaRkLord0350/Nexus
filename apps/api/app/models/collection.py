from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class CollectionType(str, PyEnum):
    manual = "manual"
    dynamic = "dynamic"


class CollectionStatus(str, PyEnum):
    draft = "draft"
    active = "active"
    archived = "archived"


class Collection(Base, TimestampMixin, TenantMixin):
    __tablename__ = "collections"
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_collection_organization_slug"),
    )

    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(1024), nullable=True)
    collection_type = Column(Enum(CollectionType, native_enum=False), nullable=False, default=CollectionType.manual)
    rules = Column(JSON, nullable=True)
    status = Column(Enum(CollectionStatus, native_enum=False), nullable=False, default=CollectionStatus.active)
    is_featured = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=0)
    seo_title = Column(String(255), nullable=True)
    seo_description = Column(String(500), nullable=True)
    seo_keywords = Column(String(500), nullable=True)
    og_image_url = Column(String(1024), nullable=True)
    canonical_url = Column(String(1024), nullable=True)
    no_index = Column(Boolean, nullable=False, default=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
