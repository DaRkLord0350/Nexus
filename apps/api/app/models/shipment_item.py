from sqlalchemy import Column, ForeignKey, Integer, String

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class ShipmentItem(Base, TimestampMixin, TenantMixin):
    __tablename__ = "shipment_items"

    shipment_id = Column(String(36), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True)
    order_item_id = Column(String(36), ForeignKey("order_items.id"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    variant_id = Column(String(36), ForeignKey("variants.id"), nullable=True, index=True)

    quantity = Column(Integer, nullable=False)
    sku = Column(String(100), nullable=False)
    product_name = Column(String(255), nullable=False)
