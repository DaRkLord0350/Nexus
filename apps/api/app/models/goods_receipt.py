from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class GoodsReceiptStatus(str, PyEnum):
    draft = "draft"
    completed = "completed"
    cancelled = "cancelled"


class GoodsReceipt(Base, TimestampMixin, TenantMixin):
    __tablename__ = "goods_receipts"
    __table_args__ = (
        UniqueConstraint("organization_id", "receipt_number", name="uq_goods_receipt_organization_number"),
    )

    receipt_number = Column(String(50), nullable=False, index=True)
    purchase_order_id = Column(String(36), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=True, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    receiver_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    received_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(Enum(GoodsReceiptStatus, native_enum=False), nullable=False, default=GoodsReceiptStatus.draft, index=True)
    notes = Column(Text, nullable=True)
