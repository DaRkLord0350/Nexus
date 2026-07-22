from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class StockTransferStatus(str, PyEnum):
    draft = "draft"
    packed = "packed"
    shipped = "shipped"
    received = "received"
    cancelled = "cancelled"


class StockTransfer(Base, TimestampMixin, TenantMixin):
    __tablename__ = "stock_transfers"
    __table_args__ = (
        UniqueConstraint("organization_id", "transfer_number", name="uq_stock_transfer_organization_number"),
    )

    transfer_number = Column(String(50), nullable=False, index=True)
    from_warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    to_warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(StockTransferStatus, native_enum=False), nullable=False, default=StockTransferStatus.draft, index=True)
    shipped_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
