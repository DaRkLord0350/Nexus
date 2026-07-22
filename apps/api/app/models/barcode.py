from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, String, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class BarcodeFormat(str, PyEnum):
    ean13 = "ean13"
    upc = "upc"
    code128 = "code128"
    qr = "qr"


class Barcode(Base, TimestampMixin, TenantMixin):
    __tablename__ = "barcodes"
    __table_args__ = (
        UniqueConstraint("organization_id", "format", "value", name="uq_barcode_organization_format_value"),
    )

    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True)
    variant_id = Column(String(36), ForeignKey("variants.id", ondelete="CASCADE"), nullable=True, index=True)
    value = Column(String(128), nullable=False, index=True)
    format = Column(Enum(BarcodeFormat, native_enum=False), nullable=False, default=BarcodeFormat.code128)
    is_primary = Column(Boolean, nullable=False, default=False)
