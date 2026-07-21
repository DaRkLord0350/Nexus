from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=1)
    slug: str | None = None
    logo: str | None = None
    industry: str | None = None
    country: str | None = None
    timezone: str | None = None
    currency: str | None = None
    subscription: str | None = None
    settings: str | None = None


class OrganizationCreateRequest(OrganizationBase):
    pass


class OrganizationUpdateRequest(BaseModel):
    name: str | None = None
    logo: str | None = None
    industry: str | None = None
    country: str | None = None
    timezone: str | None = None
    currency: str | None = None
    subscription: str | None = None
    settings: str | None = None


class OrganizationRead(OrganizationBase):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
