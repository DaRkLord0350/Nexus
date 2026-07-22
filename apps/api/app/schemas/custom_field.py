from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CustomFieldEntityType(str, Enum):
    product = "product"
    variant = "variant"
    category = "category"
    brand = "brand"
    collection = "collection"


class CustomFieldType(str, Enum):
    text = "text"
    number = "number"
    boolean = "boolean"
    date = "date"
    select = "select"
    json = "json"


class CustomFieldDefinitionCreateRequest(BaseModel):
    entity_type: CustomFieldEntityType
    name: str = Field(..., min_length=1, max_length=255)
    key: str | None = Field(default=None, max_length=100)
    field_type: CustomFieldType = CustomFieldType.text
    options: list[str] | None = None
    is_required: bool = False
    sort_order: int = 0
    is_active: bool = True


class CustomFieldDefinitionUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    field_type: CustomFieldType | None = None
    options: list[str] | None = None
    is_required: bool | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class CustomFieldDefinitionItem(BaseModel):
    id: str
    entity_type: CustomFieldEntityType
    name: str
    key: str
    field_type: CustomFieldType
    options: list[str] | None = None
    is_required: bool
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class CustomFieldDefinitionListResponse(BaseModel):
    items: list[CustomFieldDefinitionItem]
    total: int


class CustomFieldValueItem(BaseModel):
    definition_id: str
    key: str
    name: str
    field_type: CustomFieldType
    value: Any = None


class SetCustomFieldValuesRequest(BaseModel):
    values: dict[str, Any] = Field(default_factory=dict)
