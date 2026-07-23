from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.shipment_tracking import ShipmentTrackingEventRead


class ShipmentStatus(str, Enum):
    pending = "pending"
    label_generated = "label_generated"
    picked_up = "picked_up"
    in_transit = "in_transit"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    failed_delivery = "failed_delivery"
    returned_to_origin = "returned_to_origin"
    cancelled = "cancelled"


class ShipmentItemInput(BaseModel):
    order_item_id: str
    quantity: int = Field(..., gt=0)


class ShipmentCreateRequest(BaseModel):
    order_id: str
    warehouse_id: str | None = None
    shipping_provider_id: str | None = None
    items: list[ShipmentItemInput] = Field(..., min_length=1)
    weight: float | None = Field(default=None, ge=0)
    length: float | None = Field(default=None, ge=0)
    width: float | None = Field(default=None, ge=0)
    height: float | None = Field(default=None, ge=0)
    shipping_cost: float | None = Field(default=None, ge=0)
    insurance_amount: float | None = Field(default=None, ge=0)
    is_cod: bool = False
    cod_amount: float | None = Field(default=None, ge=0)
    service_type: str | None = None
    notes: str | None = None


class ShipmentUpdateRequest(BaseModel):
    weight: float | None = Field(default=None, ge=0)
    length: float | None = Field(default=None, ge=0)
    width: float | None = Field(default=None, ge=0)
    height: float | None = Field(default=None, ge=0)
    shipping_cost: float | None = Field(default=None, ge=0)
    insurance_amount: float | None = Field(default=None, ge=0)
    service_type: str | None = None
    expected_delivery_date: datetime | None = None
    notes: str | None = None


class ShipmentFailDeliveryRequest(BaseModel):
    reason: str | None = None


class ShipmentCancelRequest(BaseModel):
    reason: str | None = None


class ShipmentItemRead(BaseModel):
    id: str
    shipment_id: str
    order_item_id: str
    product_id: str
    variant_id: str | None = None
    quantity: int
    sku: str
    product_name: str

    model_config = {"from_attributes": True}


class ShipmentRead(BaseModel):
    id: str
    shipment_number: str
    order_id: str
    warehouse_id: str
    shipping_provider_id: str | None = None
    status: ShipmentStatus
    tracking_number: str | None = None
    carrier_name: str | None = None
    service_type: str | None = None
    weight: float | None = None
    length: float | None = None
    width: float | None = None
    height: float | None = None
    shipping_cost: float
    insurance_amount: float | None = None
    is_cod: bool
    cod_amount: float | None = None
    expected_delivery_date: datetime | None = None
    picked_up_at: datetime | None = None
    delivered_at: datetime | None = None
    cancelled_at: datetime | None = None
    delivery_attempts: int
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ShipmentDetail(ShipmentRead):
    items: list[ShipmentItemRead] = Field(default_factory=list)


class CustomerShipmentTrackingRead(ShipmentDetail):
    tracking_events: list[ShipmentTrackingEventRead] = Field(default_factory=list)


class ShipmentListResponse(BaseModel):
    items: list[ShipmentRead]
    total: int
    limit: int
    offset: int
