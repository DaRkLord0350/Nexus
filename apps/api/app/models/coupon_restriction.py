from sqlalchemy import Column, ForeignKey, String, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class CouponProduct(Base, TimestampMixin, TenantMixin):
    __tablename__ = "coupon_products"
    __table_args__ = (UniqueConstraint("coupon_id", "product_id", name="uq_coupon_product"),)

    coupon_id = Column(String(36), ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)


class CouponCategory(Base, TimestampMixin, TenantMixin):
    __tablename__ = "coupon_categories"
    __table_args__ = (UniqueConstraint("coupon_id", "category_id", name="uq_coupon_category"),)

    coupon_id = Column(String(36), ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(String(36), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)


class CouponCollection(Base, TimestampMixin, TenantMixin):
    __tablename__ = "coupon_collections"
    __table_args__ = (UniqueConstraint("coupon_id", "collection_id", name="uq_coupon_collection"),)

    coupon_id = Column(String(36), ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False, index=True)
    collection_id = Column(String(36), ForeignKey("collections.id", ondelete="CASCADE"), nullable=False, index=True)
