from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.schemas.shipping_rate import (
    RateCompareRequest,
    RateCompareResponse,
    ShippingRateCreateRequest,
    ShippingRateListResponse,
    ShippingRateRead,
    ShippingRateUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.shipping_rate_service import ShippingRateService

router = APIRouter(prefix="/rates", tags=["shipping-rates"])


def _rate_service(db: AsyncSession, current_user) -> ShippingRateService:
    return ShippingRateService(db, current_user.organization_id, current_user.is_superuser)


@router.post("/compare", response_model=RateCompareResponse)
async def compare_shipping_rates(
    data: RateCompareRequest,
    current_user=Depends(require_permission("shipping.rates.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _rate_service(db, current_user)
    quotes = await service.compare_rates(data)
    return {"quotes": quotes}


@router.get("/", response_model=ShippingRateListResponse)
async def list_shipping_rates(
    shipping_provider_id: str = Query(...),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("shipping.rates.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _rate_service(db, current_user)
    items, total = await service.list_rates_for_provider(shipping_provider_id, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=ShippingRateRead, status_code=status.HTTP_201_CREATED)
async def create_shipping_rate(
    data: ShippingRateCreateRequest,
    current_user=Depends(require_permission("shipping.rates.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _rate_service(db, current_user)
    rate = await service.create_rate(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="shipping", entity="ShippingRate", entity_id=rate.id,
        user_id=current_user.id, after={"name": rate.name, "shipping_provider_id": rate.shipping_provider_id}, context=audit_context,
    )
    return rate


@router.get("/{rate_id}", response_model=ShippingRateRead)
async def get_shipping_rate(rate_id: str, current_user=Depends(require_permission("shipping.rates.view")), db: AsyncSession = Depends(get_db)):
    service = _rate_service(db, current_user)
    rate = await service.get_rate(rate_id)
    if not rate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipping rate not found.")
    return rate


@router.patch("/{rate_id}", response_model=ShippingRateRead)
async def update_shipping_rate(
    rate_id: str,
    data: ShippingRateUpdateRequest,
    current_user=Depends(require_permission("shipping.rates.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _rate_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    rate = await service.update_rate(rate_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="shipping", entity="ShippingRate", entity_id=rate.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return rate


@router.delete("/{rate_id}")
async def delete_shipping_rate(
    rate_id: str,
    current_user=Depends(require_permission("shipping.rates.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _rate_service(db, current_user)
    await service.delete_rate(rate_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="shipping", entity="ShippingRate", entity_id=rate_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Shipping rate deleted successfully."}
