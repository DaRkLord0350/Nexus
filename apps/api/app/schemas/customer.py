from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class CustomerCreateRequest(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=128)
    last_name: str = Field(..., min_length=1, max_length=128)
    phone: str | None = None
    password: str | None = Field(default=None, min_length=8, max_length=255)
    accepts_marketing: bool = False
    notes: str | None = None


class CustomerUpdateRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=128)
    last_name: str | None = Field(default=None, min_length=1, max_length=128)
    phone: str | None = None
    is_active: bool | None = None
    accepts_marketing: bool | None = None
    notes: str | None = None


class CustomerSelfUpdateRequest(BaseModel):
    """Fields a customer may edit on their own profile via the portal —
    deliberately excludes is_active/notes, which are staff-only."""

    first_name: str | None = Field(default=None, min_length=1, max_length=128)
    last_name: str | None = Field(default=None, min_length=1, max_length=128)
    phone: str | None = None
    accepts_marketing: bool | None = None


class CustomerItem(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: str | None = None
    is_guest: bool
    is_active: bool
    is_verified: bool
    accepts_marketing: bool
    last_login_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerListResponse(BaseModel):
    items: list[CustomerItem]
    total: int
    limit: int
    offset: int


class BulkDeleteRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1)


class CustomerRegisterRequest(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=128)
    last_name: str = Field(..., min_length=1, max_length=128)
    phone: str | None = None
    password: str = Field(..., min_length=8, max_length=255)
    accepts_marketing: bool = False
    organization_id: str


class CustomerLoginRequest(BaseModel):
    email: EmailStr
    password: str
    organization_id: str


class CustomerTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    customer: CustomerItem
