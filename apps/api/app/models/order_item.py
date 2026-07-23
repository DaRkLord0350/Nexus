from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class OrderItem(Base, TimestampMixin, TenantMixin):
    __tablename__ = "order_items"

    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    variant_id = Column(String(36), ForeignKey("variants.id"), nullable=True, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=True, index=True)

    sku = Column(String(100), nullable=False)
    product_name = Column(String(255), nullable=False)

    quantity = Column(Integer, nullable=False)
    quantity_fulfilled = Column(Integer, nullable=False, default=0)
    quantity_returned = Column(Integer, nullable=False, default=0)

    unit_price = Column(Float, nullable=False, default=0)
    discount_amount = Column(Float, nullable=False, default=0)
    tax_amount = Column(Float, nullable=False, default=0)
    total = Column(Float, nullable=False, default=0)

    gift_note = Column(Text, nullable=True)
