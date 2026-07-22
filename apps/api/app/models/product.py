from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class ProductStatus(str, PyEnum):
    draft = "draft"
    published = "published"
    archived = "archived"


class Product(Base, TimestampMixin, TenantMixin):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_product_organization_slug"),
        UniqueConstraint("organization_id", "sku", name="uq_product_organization_sku"),
    )

    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    sku = Column(String(100), nullable=False, index=True)
    barcode = Column(String(100), nullable=True, index=True)
    brand_id = Column(String(36), ForeignKey("brands.id"), nullable=True, index=True)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=True, index=True)
    tax_class_id = Column(String(36), ForeignKey("tax_classes.id"), nullable=True, index=True)
    product_type_id = Column(String(36), ForeignKey("product_types.id"), nullable=True, index=True)
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)
    status = Column(Enum(ProductStatus, native_enum=False), nullable=False, default=ProductStatus.draft, index=True)
    seo_title = Column(String(255), nullable=True)
    seo_description = Column(String(500), nullable=True)
    seo_keywords = Column(String(500), nullable=True)
    og_image_url = Column(String(1024), nullable=True)
    canonical_url = Column(String(1024), nullable=True)
    no_index = Column(Boolean, nullable=False, default=False)
    length = Column(Float, nullable=True)
    width = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    dimension_unit = Column(String(16), nullable=True)
    weight = Column(Float, nullable=True)
    weight_unit = Column(String(16), nullable=True)
    origin_country = Column(String(128), nullable=True)
    vendor = Column(String(255), nullable=True)
    search_keywords = Column(Text, nullable=True)
    track_inventory = Column(Boolean, nullable=False, default=True)
    allow_backorders = Column(Boolean, nullable=False, default=False)
    has_variants = Column(Boolean, nullable=False, default=False)
    is_featured = Column(Boolean, nullable=False, default=False)
    published_at = Column(DateTime, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
