from pydantic import BaseModel, EmailStr, Field


class InviteMemberRequest(BaseModel):
    email: EmailStr


class AcceptInvitationRequest(BaseModel):
    token: str
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    password: str = Field(..., min_length=10)
