from datetime import datetime

from pydantic import BaseModel, Field


class TagCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str | None = Field(default=None, max_length=100)


class TagUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    slug: str | None = Field(default=None, max_length=100)


class TagItem(BaseModel):
    id: str
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class TagListResponse(BaseModel):
    items: list[TagItem]
    total: int
    limit: int
    offset: int
