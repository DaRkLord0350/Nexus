from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class PurchaseOrderStatus(str, PyEnum):
    draft = "draft"
    sent = "sent"
    partially_received = "partially_received"
    received = "received"
    cancelled = "cancelled"


class PurchaseOrder(Base, TimestampMixin, TenantMixin):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        UniqueConstraint("organization_id", "po_number", name="uq_purchase_order_organization_number"),
    )

    po_number = Column(String(50), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_email = Column(String(255), nullable=True)
    supplier_phone = Column(String(50), nullable=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(PurchaseOrderStatus, native_enum=False), nullable=False, default=PurchaseOrderStatus.draft, index=True)
    currency = Column(String(3), nullable=False, default="USD")
    subtotal = Column(Float, nullable=False, default=0)
    tax_amount = Column(Float, nullable=False, default=0)
    shipping_amount = Column(Float, nullable=False, default=0)
    total = Column(Float, nullable=False, default=0)
    expected_date = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
