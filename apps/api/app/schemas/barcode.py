from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class BarcodeFormat(str, Enum):
    ean13 = "ean13"
    upc = "upc"
    code128 = "code128"
    qr = "qr"


class BarcodeCreateRequest(BaseModel):
    product_id: str | None = None
    variant_id: str | None = None
    value: str = Field(..., min_length=1, max_length=128)
    format: BarcodeFormat = BarcodeFormat.code128
    is_primary: bool = False


class BarcodeUpdateRequest(BaseModel):
    value: str | None = Field(default=None, min_length=1, max_length=128)
    format: BarcodeFormat | None = None
    is_primary: bool | None = None


class BarcodeItem(BaseModel):
    id: str
    product_id: str | None = None
    variant_id: str | None = None
    value: str
    format: BarcodeFormat
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class BarcodeListResponse(BaseModel):
    items: list[BarcodeItem]
    total: int
    limit: int
    offset: int


class QRCodeCreateRequest(BaseModel):
    entity_type: str = Field(..., min_length=1, max_length=32)
    entity_id: str = Field(..., min_length=1, max_length=36)
    value: str = Field(..., min_length=1, max_length=255)
    image_url: str | None = None


class QRCodeUpdateRequest(BaseModel):
    value: str | None = Field(default=None, min_length=1, max_length=255)
    image_url: str | None = None


class QRCodeItem(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    value: str
    image_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class QRCodeListResponse(BaseModel):
    items: list[QRCodeItem]
    total: int
    limit: int
    offset: int


class BulkDeleteRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1)
