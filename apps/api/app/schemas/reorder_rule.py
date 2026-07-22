from datetime import datetime

from pydantic import BaseModel, Field


class ReorderRuleCreateRequest(BaseModel):
    product_id: str
    variant_id: str | None = None
    warehouse_id: str
    minimum_stock: int = Field(..., ge=0)
    maximum_stock: int | None = Field(default=None, ge=0)
    reorder_quantity: int = Field(..., gt=0)
    supplier_name: str | None = None
    lead_time_days: int | None = Field(default=None, ge=0)
    is_active: bool = True


class ReorderRuleUpdateRequest(BaseModel):
    minimum_stock: int | None = Field(default=None, ge=0)
    maximum_stock: int | None = Field(default=None, ge=0)
    reorder_quantity: int | None = Field(default=None, gt=0)
    supplier_name: str | None = None
    lead_time_days: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ReorderRuleItem(BaseModel):
    id: str
    product_id: str
    variant_id: str | None = None
    warehouse_id: str
    minimum_stock: int
    maximum_stock: int | None = None
    reorder_quantity: int
    supplier_name: str | None = None
    lead_time_days: int | None = None
    is_active: bool
    last_triggered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class ReorderRuleListResponse(BaseModel):
    items: list[ReorderRuleItem]
    total: int
    limit: int
    offset: int


class BulkDeleteRequest(BaseModel):
    ids: list[str] = Field(..., min_length=1)
