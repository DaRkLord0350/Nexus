from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, Text

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class ReturnItemCondition(str, PyEnum):
    unopened = "unopened"
    opened = "opened"
    damaged = "damaged"
    defective = "defective"


class ReturnItem(Base, TimestampMixin, TenantMixin):
    __tablename__ = "return_items"

    return_request_id = Column(String(36), ForeignKey("return_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    order_item_id = Column(String(36), ForeignKey("order_items.id"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    variant_id = Column(String(36), ForeignKey("variants.id"), nullable=True, index=True)

    quantity = Column(Integer, nullable=False)
    reason_code = Column(String(64), nullable=True)
    condition = Column(Enum(ReturnItemCondition, native_enum=False), nullable=True)
    image_urls = Column(Text, nullable=True)

    restocked = Column(Boolean, nullable=False, default=False)
    restocked_quantity = Column(Integer, nullable=False, default=0)
