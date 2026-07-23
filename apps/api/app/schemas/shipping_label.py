from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ShippingLabelType(str, Enum):
    label = "label"
    packing_slip = "packing_slip"
    manifest = "manifest"
    return_label = "return_label"


class ShippingLabelRead(BaseModel):
    id: str
    shipment_id: str
    label_type: ShippingLabelType
    format: str
    generated_by: str | None = None
    generated_at: datetime

    model_config = {"from_attributes": True}


class ManifestGenerateRequest(BaseModel):
    warehouse_id: str
    shipment_ids: list[str] = Field(..., min_length=1)


class BulkLabelsRequest(BaseModel):
    shipment_ids: list[str] = Field(..., min_length=1)
