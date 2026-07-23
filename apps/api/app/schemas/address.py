from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AddressType(str, Enum):
    billing = "billing"
    shipping = "shipping"
    both = "both"


class AddressCreateRequest(BaseModel):
    label: str | None = Field(default=None, max_length=64)
    address_type: AddressType = AddressType.shipping
    first_name: str = Field(..., min_length=1, max_length=128)
    last_name: str = Field(..., min_length=1, max_length=128)
    company: str | None = None
    phone: str | None = None
    line1: str = Field(..., min_length=1, max_length=255)
    line2: str | None = None
    city: str = Field(..., min_length=1, max_length=128)
    state: str | None = None
    postal_code: str | None = None
    country: str = Field(..., min_length=2, max_length=2)
    is_default: bool = False


class AddressUpdateRequest(BaseModel):
    label: str | None = Field(default=None, max_length=64)
    address_type: AddressType | None = None
    first_name: str | None = Field(default=None, min_length=1, max_length=128)
    last_name: str | None = Field(default=None, min_length=1, max_length=128)
    company: str | None = None
    phone: str | None = None
    line1: str | None = Field(default=None, min_length=1, max_length=255)
    line2: str | None = None
    city: str | None = Field(default=None, min_length=1, max_length=128)
    state: str | None = None
    postal_code: str | None = None
    country: str | None = Field(default=None, min_length=2, max_length=2)
    is_default: bool | None = None


class AddressItem(BaseModel):
    id: str
    customer_id: str
    label: str | None = None
    address_type: AddressType
    first_name: str
    last_name: str
    company: str | None = None
    phone: str | None = None
    line1: str
    line2: str | None = None
    city: str
    state: str | None = None
    postal_code: str | None = None
    country: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AddressListResponse(BaseModel):
    items: list[AddressItem]
    total: int
    limit: int
    offset: int
