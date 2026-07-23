from enum import Enum

from pydantic import BaseModel, Field


class ShippingRuleConditionType(str, Enum):
    weight_greater_than = "weight_greater_than"
    weight_less_than = "weight_less_than"
    is_cod = "is_cod"
    destination_state = "destination_state"
    destination_country = "destination_country"
    order_value_greater_than = "order_value_greater_than"


class ShippingRuleActionType(str, Enum):
    assign_provider = "assign_provider"
    exclude_provider = "exclude_provider"
    prefer_warehouse = "prefer_warehouse"


class ShippingRuleCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    priority: int = 0
    is_active: bool = True
    condition_type: ShippingRuleConditionType
    condition_value: str = Field(..., min_length=1, max_length=255)
    action_type: ShippingRuleActionType
    action_value: str = Field(..., min_length=1, max_length=64)


class ShippingRuleUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    priority: int | None = None
    is_active: bool | None = None
    condition_type: ShippingRuleConditionType | None = None
    condition_value: str | None = Field(default=None, min_length=1, max_length=255)
    action_type: ShippingRuleActionType | None = None
    action_value: str | None = Field(default=None, min_length=1, max_length=64)


class ShippingRuleRead(BaseModel):
    id: str
    name: str
    priority: int
    is_active: bool
    condition_type: ShippingRuleConditionType
    condition_value: str
    action_type: ShippingRuleActionType
    action_value: str

    model_config = {"from_attributes": True}


class ShippingRuleListResponse(BaseModel):
    items: list[ShippingRuleRead]
    total: int
    limit: int
    offset: int


class ShippingRuleEvaluateRequest(BaseModel):
    weight: float = 0.0
    is_cod: bool = False
    destination_state: str | None = None
    destination_country: str | None = None
    order_value: float = 0.0


class ShippingRuleEvaluateResponse(BaseModel):
    preferred_provider_id: str | None = None
    excluded_provider_ids: list[str] = Field(default_factory=list)
    preferred_warehouse_id: str | None = None
    matched_rule_ids: list[str] = Field(default_factory=list)
