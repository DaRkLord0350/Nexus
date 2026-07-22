from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class SlugRedirectEntityType(str, Enum):
    category = "category"
    brand = "brand"
    product = "product"
    collection = "collection"


class SlugRedirectItem(BaseModel):
    id: str
    entity_type: str
    old_slug: str
    new_slug: str
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class SlugRedirectListResponse(BaseModel):
    items: list[SlugRedirectItem]


class SlugRedirectResolveResponse(BaseModel):
    slug: str | None = None
