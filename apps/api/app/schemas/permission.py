from pydantic import BaseModel


class PermissionRead(BaseModel):
    code: str
    name: str | None = None
    description: str | None = None

    class Config:
        orm_mode = True
