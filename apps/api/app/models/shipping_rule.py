from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, Enum, Integer, String

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class ShippingRuleConditionType(str, PyEnum):
    weight_greater_than = "weight_greater_than"
    weight_less_than = "weight_less_than"
    is_cod = "is_cod"
    destination_state = "destination_state"
    destination_country = "destination_country"
    order_value_greater_than = "order_value_greater_than"


class ShippingRuleActionType(str, PyEnum):
    assign_provider = "assign_provider"
    exclude_provider = "exclude_provider"
    prefer_warehouse = "prefer_warehouse"


class ShippingRule(Base, TimestampMixin, TenantMixin):
    __tablename__ = "shipping_rules"

    name = Column(String(255), nullable=False)
    priority = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)

    condition_type = Column(Enum(ShippingRuleConditionType, native_enum=False), nullable=False)
    condition_value = Column(String(255), nullable=False)

    action_type = Column(Enum(ShippingRuleActionType, native_enum=False), nullable=False)
    action_value = Column(String(64), nullable=False)
