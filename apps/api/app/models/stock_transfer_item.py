from sqlalchemy import Column, ForeignKey, Integer, String

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class StockTransferItem(Base, TimestampMixin, TenantMixin):
    __tablename__ = "stock_transfer_items"

    stock_transfer_id = Column(String(36), ForeignKey("stock_transfers.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(String(36), ForeignKey("variants.id", ondelete="CASCADE"), nullable=True, index=True)
    quantity_requested = Column(Integer, nullable=False)
    quantity_shipped = Column(Integer, nullable=False, default=0)
    quantity_received = Column(Integer, nullable=False, default=0)
    batch_id = Column(String(36), ForeignKey("batches.id", ondelete="SET NULL"), nullable=True, index=True)
    notes = Column(String(500), nullable=True)
