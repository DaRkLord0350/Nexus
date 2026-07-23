from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class InvoiceStatus(str, PyEnum):
    issued = "issued"
    paid = "paid"
    void = "void"


class Invoice(Base, TimestampMixin, TenantMixin):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("organization_id", "invoice_number", name="uq_invoice_organization_number"),
        UniqueConstraint("organization_id", "order_id", name="uq_invoice_organization_order"),
    )

    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_number = Column(String(50), nullable=False, index=True)
    status = Column(Enum(InvoiceStatus, native_enum=False), nullable=False, default=InvoiceStatus.issued, index=True)
    currency = Column(String(3), nullable=False, default="USD")
    subtotal = Column(Float, nullable=False, default=0)
    discount_amount = Column(Float, nullable=False, default=0)
    tax_amount = Column(Float, nullable=False, default=0)
    shipping_amount = Column(Float, nullable=False, default=0)
    total = Column(Float, nullable=False, default=0)
    amount_paid = Column(Float, nullable=False, default=0)
    amount_due = Column(Float, nullable=False, default=0)
    issued_at = Column(DateTime, nullable=True)
    due_at = Column(DateTime, nullable=True)
    voided_at = Column(DateTime, nullable=True)
    void_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
