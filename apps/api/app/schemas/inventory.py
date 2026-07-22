from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class InventoryTransactionType(str, Enum):
    receive = "receive"
    sale = "sale"
    return_ = "return"
    transfer = "transfer"
    adjustment = "adjustment"
    damage = "damage"
    cycle_count = "cycle_count"
    manufacturing = "manufacturing"
    purchase = "purchase"


class InventoryUpdateRequest(BaseModel):
    bin_id: str | None = None
    minimum_stock: int | None = None
    maximum_stock: int | None = None
    reorder_point: int | None = None


class InventoryItem(BaseModel):
    id: str
    product_id: str
    variant_id: str | None = None
    warehouse_id: str
    bin_id: str | None = None
    quantity_available: int
    quantity_reserved: int
    quantity_incoming: int
    quantity_damaged: int
    quantity_returned: int
    minimum_stock: int | None = None
    maximum_stock: int | None = None
    reorder_point: int | None = None
    average_cost: float | None = None
    last_counted_at: datetime | None = None
    low_stock_notified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class InventoryListResponse(BaseModel):
    items: list[InventoryItem]
    total: int
    limit: int
    offset: int


class InventoryTransactionItem(BaseModel):
    id: str
    inventory_id: str
    product_id: str
    variant_id: str | None = None
    warehouse_id: str
    batch_id: str | None = None
    serial_number_id: str | None = None
    type: InventoryTransactionType
    quantity: int
    quantity_before: int | None = None
    quantity_after: int | None = None
    reference_type: str | None = None
    reference_id: str | None = None
    user_id: str | None = None
    notes: str | None = None
    occurred_at: datetime
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class InventoryTransactionListResponse(BaseModel):
    items: list[InventoryTransactionItem]
    total: int
    limit: int
    offset: int
