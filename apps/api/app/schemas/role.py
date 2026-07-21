from datetime import datetime
from pydantic import BaseModel, Field


class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = None


class RoleCreateRequest(RoleBase):
    permission_codes: list[str] = []


class RoleRead(RoleBase):
    id: str
    organization_id: str
    built_in: bool
    permissions: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
