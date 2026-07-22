from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class GoodsReceiptItem(Base, TimestampMixin, TenantMixin):
    __tablename__ = "goods_receipt_items"

    goods_receipt_id = Column(String(36), ForeignKey("goods_receipts.id", ondelete="CASCADE"), nullable=False, index=True)
    purchase_order_item_id = Column(String(36), ForeignKey("purchase_order_items.id", ondelete="SET NULL"), nullable=True, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(String(36), ForeignKey("variants.id", ondelete="CASCADE"), nullable=True, index=True)
    quantity_received = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=True)
    batch_number = Column(String(100), nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    manufactured_date = Column(DateTime, nullable=True)
    bin_id = Column(String(36), ForeignKey("warehouse_bins.id", ondelete="SET NULL"), nullable=True, index=True)
    notes = Column(String(500), nullable=True)
