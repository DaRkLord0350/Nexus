from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class CartItem(Base, TimestampMixin, TenantMixin):
    __tablename__ = "cart_items"

    cart_id = Column(String(36), ForeignKey("carts.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(String(36), ForeignKey("variants.id", ondelete="CASCADE"), nullable=True, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False, default=0)
    saved_for_later = Column(Boolean, nullable=False, default=False)
    gift_note = Column(Text, nullable=True)
