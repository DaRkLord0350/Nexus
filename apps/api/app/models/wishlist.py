from sqlalchemy import Column, ForeignKey, String, Text

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class Wishlist(Base, TimestampMixin, TenantMixin):
    __tablename__ = "wishlists"

    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(String(36), ForeignKey("variants.id", ondelete="CASCADE"), nullable=True, index=True)
    notes = Column(Text, nullable=True)
