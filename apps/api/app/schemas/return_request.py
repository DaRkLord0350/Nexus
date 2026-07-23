from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ReturnStatus(str, Enum):
    requested = "requested"
    approved = "approved"
    rejected = "rejected"
    awaiting_pickup = "awaiting_pickup"
    in_transit = "in_transit"
    received = "received"
    inspecting = "inspecting"
    completed = "completed"
    cancelled = "cancelled"


class ReturnResolution(str, Enum):
    refund = "refund"
    replacement = "replacement"
    exchange = "exchange"
    repair = "repair"
    store_credit = "store_credit"


class ReturnItemCondition(str, Enum):
    unopened = "unopened"
    opened = "opened"
    damaged = "damaged"
    defective = "defective"


class ReturnItemInput(BaseModel):
    order_item_id: str
    quantity: int = Field(..., gt=0)
    reason_code: str | None = Field(default=None, max_length=64)
    image_urls: list[str] = Field(default_factory=list)


class ReturnRequestCreateRequest(BaseModel):
    order_id: str
    reason_code: str = Field(..., min_length=1, max_length=64)
    reason_notes: str | None = None
    items: list[ReturnItemInput] = Field(..., min_length=1)


class ReturnApproveRequest(BaseModel):
    resolution: ReturnResolution | None = None


class ReturnRejectRequest(BaseModel):
    reason: str | None = None


class ReturnReceiveRequest(BaseModel):
    warehouse_id: str | None = None


class ReturnItemInspectionRequest(BaseModel):
    condition: ReturnItemCondition
    reason_code: str | None = None


class ReturnCompleteRequest(BaseModel):
    resolution: ReturnResolution
    restock: bool = True


class ReturnCancelRequest(BaseModel):
    reason: str | None = None


class ReturnItemRead(BaseModel):
    id: str
    return_request_id: str
    order_item_id: str
    product_id: str
    variant_id: str | None = None
    quantity: int
    reason_code: str | None = None
    condition: ReturnItemCondition | None = None
    image_urls: str | None = None
    restocked: bool
    restocked_quantity: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReturnRequestRead(BaseModel):
    id: str
    return_number: str
    order_id: str
    customer_id: str
    warehouse_id: str | None = None
    status: ReturnStatus
    resolution: ReturnResolution | None = None
    reason_code: str
    reason_notes: str | None = None
    inspection_notes: str | None = None
    inspected_by: str | None = None
    inspected_at: datetime | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    rejected_reason: str | None = None
    requested_at: datetime
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReturnRequestDetail(ReturnRequestRead):
    items: list[ReturnItemRead] = Field(default_factory=list)


class ReturnRequestListResponse(BaseModel):
    items: list[ReturnRequestRead]
    total: int
    limit: int
    offset: int
