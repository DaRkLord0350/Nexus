from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class ProductPrice(Base, TimestampMixin, TenantMixin):
    __tablename__ = "product_prices"

    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(String(36), ForeignKey("variants.id", ondelete="CASCADE"), nullable=True, index=True)
    currency = Column(String(3), nullable=False, index=True)
    mrp = Column(Float, nullable=True)
    selling_price = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=True)
    compare_price = Column(Float, nullable=True)
    min_price = Column(Float, nullable=True)
    max_price = Column(Float, nullable=True)
    customer_group = Column(String(64), nullable=True, index=True)
    region = Column(String(64), nullable=True, index=True)
    effective_from = Column(DateTime, nullable=True)
    effective_to = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
