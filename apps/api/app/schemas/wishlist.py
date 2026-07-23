from datetime import datetime

from pydantic import BaseModel, Field


class WishlistItemCreateRequest(BaseModel):
    product_id: str
    variant_id: str | None = None
    notes: str | None = None


class WishlistItemRead(BaseModel):
    id: str
    customer_id: str
    product_id: str
    variant_id: str | None = None
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WishlistListResponse(BaseModel):
    items: list[WishlistItemRead]
    total: int
    limit: int
    offset: int
