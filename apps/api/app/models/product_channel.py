from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class ProductChannel(Base, TimestampMixin, TenantMixin):
    __tablename__ = "product_channels"
    __table_args__ = (
        UniqueConstraint("product_id", "channel_id", name="uq_product_channel"),
    )

    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    channel_id = Column(String(36), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True)
    is_published = Column(Boolean, nullable=False, default=False)
    published_at = Column(DateTime, nullable=True)
