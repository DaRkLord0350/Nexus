from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class ShippingRate(Base, TimestampMixin, TenantMixin):
    __tablename__ = "shipping_rates"

    shipping_provider_id = Column(String(36), ForeignKey("shipping_providers.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)

    origin_country = Column(String(2), nullable=True)
    destination_country = Column(String(2), nullable=True, index=True)
    destination_state = Column(String(64), nullable=True, index=True)

    min_weight = Column(Float, nullable=True)
    max_weight = Column(Float, nullable=True)

    base_price = Column(Float, nullable=False, default=0)
    price_per_kg = Column(Float, nullable=True)
    cod_fee = Column(Float, nullable=True)
    insurance_fee = Column(Float, nullable=True)

    transit_days_min = Column(Integer, nullable=True)
    transit_days_max = Column(Integer, nullable=True)
    delivery_rating = Column(Float, nullable=True)

    is_active = Column(Boolean, nullable=False, default=True)
