from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class WarehouseType(str, Enum):
    main = "main"
    retail = "retail"
    returns = "returns"
    third_party = "third_party"


class WarehouseZoneType(str, Enum):
    receiving = "receiving"
    storage = "storage"
    picking = "picking"
    packing = "packing"
    returns = "returns"
    damaged = "damaged"


class WarehouseBinStatus(str, Enum):
    active = "active"
    full = "full"
    blocked = "blocked"
    inactive = "inactive"


class WarehouseCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    warehouse_type: WarehouseType = WarehouseType.main
    email: str | None = None
    phone: str | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    zipcode: str | None = None
    address: str | None = None
    is_default: bool = False
    is_active: bool = True


class WarehouseUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, min_length=1, max_length=50)
    warehouse_type: WarehouseType | None = None
    email: str | None = None
    phone: str | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    zipcode: str | None = None
    address: str | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class WarehouseItem(BaseModel):
    id: str
    name: str
    code: str
    warehouse_type: WarehouseType
    email: str | None = None
    phone: str | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    zipcode: str | None = None
    address: str | None = None
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class WarehouseListResponse(BaseModel):
    items: list[WarehouseItem]
    total: int
    limit: int
    offset: int


class WarehouseZoneCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    zone_type: WarehouseZoneType = WarehouseZoneType.storage
    description: str | None = None
    is_active: bool = True


class WarehouseZoneUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, min_length=1, max_length=50)
    zone_type: WarehouseZoneType | None = None
    description: str | None = None
    is_active: bool | None = None


class WarehouseZoneItem(BaseModel):
    id: str
    warehouse_id: str
    name: str
    code: str
    zone_type: WarehouseZoneType
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class WarehouseZoneListResponse(BaseModel):
    items: list[WarehouseZoneItem]
    total: int
    limit: int
    offset: int


class WarehouseBinCreateRequest(BaseModel):
    zone_id: str | None = None
    code: str = Field(..., min_length=1, max_length=50)
    aisle: str | None = None
    rack: str | None = None
    shelf: str | None = None
    bin_number: str | None = None
    capacity: int | None = None
    status: WarehouseBinStatus = WarehouseBinStatus.active


class WarehouseBinUpdateRequest(BaseModel):
    zone_id: str | None = None
    code: str | None = Field(default=None, min_length=1, max_length=50)
    aisle: str | None = None
    rack: str | None = None
    shelf: str | None = None
    bin_number: str | None = None
    capacity: int | None = None
    status: WarehouseBinStatus | None = None


class WarehouseBinItem(BaseModel):
    id: str
    warehouse_id: str
    zone_id: str | None = None
    code: str
    aisle: str | None = None
    rack: str | None = None
    shelf: str | None = None
    bin_number: str | None = None
    capacity: int | None = None
    status: WarehouseBinStatus
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class WarehouseBinListResponse(BaseModel):
    items: list[WarehouseBinItem]
    total: int
    limit: int
    offset: int


class BulkDeleteRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1)
