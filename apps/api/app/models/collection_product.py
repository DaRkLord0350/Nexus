from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class CollectionProduct(Base, TimestampMixin, TenantMixin):
    __tablename__ = "collection_products"
    __table_args__ = (
        UniqueConstraint("collection_id", "product_id", name="uq_collection_product"),
    )

    collection_id = Column(String(36), ForeignKey("collections.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    sort_order = Column(Integer, nullable=False, default=0)
