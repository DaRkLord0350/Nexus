from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class InventoryTransactionType(str, PyEnum):
    receive = "receive"
    sale = "sale"
    return_ = "return"
    transfer = "transfer"
    adjustment = "adjustment"
    damage = "damage"
    cycle_count = "cycle_count"
    manufacturing = "manufacturing"
    purchase = "purchase"


class InventoryTransaction(Base, TimestampMixin, TenantMixin):
    __tablename__ = "inventory_transactions"

    inventory_id = Column(String(36), ForeignKey("inventory.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(String(36), ForeignKey("variants.id", ondelete="CASCADE"), nullable=True, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id = Column(String(36), ForeignKey("batches.id", ondelete="SET NULL"), nullable=True, index=True)
    serial_number_id = Column(String(36), ForeignKey("serial_numbers.id", ondelete="SET NULL"), nullable=True, index=True)
    #
    # values_callable is required here (unlike other Enum columns in this
    # codebase) because `return` is a Python keyword: the member is named
    # `return_` but must be stored/compared as the string "return". Without
    # it SQLAlchemy stores enum members by .name, not .value.
    type = Column(
        Enum(InventoryTransactionType, native_enum=False, values_callable=lambda enum_cls: [e.value for e in enum_cls]),
        nullable=False,
        index=True,
    )
    quantity = Column(Integer, nullable=False)
    quantity_before = Column(Integer, nullable=True)
    quantity_after = Column(Integer, nullable=True)

    reference_type = Column(String(50), nullable=True, index=True)
    reference_id = Column(String(36), nullable=True, index=True)

    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    occurred_at = Column(DateTime, default=datetime.utcnow, nullable=False)
