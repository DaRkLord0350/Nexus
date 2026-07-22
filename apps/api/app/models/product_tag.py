from sqlalchemy import Column, ForeignKey, String, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class ProductTag(Base, TimestampMixin, TenantMixin):
    __tablename__ = "product_tags"
    __table_args__ = (
        UniqueConstraint("product_id", "tag_id", name="uq_product_tag"),
    )

    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    tag_id = Column(String(36), ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True)
