from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_current_active_user, get_db, require_permission
from app.schemas.product_price import (
    BulkDeleteRequest,
    ProductPriceCreateRequest,
    ProductPriceItem,
    ProductPriceListResponse,
    ProductPriceUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.pricing_service import PricingService

router = APIRouter(prefix="/pricing", tags=["catalog-pricing"])


def _pricing_service(db: AsyncSession, current_user) -> PricingService:
    return PricingService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=ProductPriceListResponse)
async def list_prices(
    product_id: str = Query(...),
    variant_id: str | None = Query(None),
    currency: str | None = Query(None),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("catalog.products.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _pricing_service(db, current_user)
    items, total = await service.list_prices(product_id, variant_id if variant_id is not None else "__unset__", currency, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/resolve", response_model=ProductPriceItem)
async def resolve_price(
    product_id: str = Query(...),
    currency: str = Query(...),
    variant_id: str | None = Query(None),
    customer_group: str | None = Query(None),
    region: str | None = Query(None),
    current_user=Depends(require_permission("catalog.products.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _pricing_service(db, current_user)
    price = await service.resolve_price(product_id, currency, variant_id, customer_group, region)
    if not price:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching price found.")
    return price


@router.post("/", response_model=ProductPriceItem, status_code=status.HTTP_201_CREATED)
async def create_price(
    data: ProductPriceCreateRequest,
    current_user=Depends(require_permission("catalog.pricing.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _pricing_service(db, current_user)
    price = await service.create_price(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="price_change", module="catalog", entity="ProductPrice", entity_id=price.id,
        user_id=current_user.id, after={"product_id": price.product_id, "selling_price": price.selling_price, "currency": price.currency}, context=audit_context,
    )
    return price


@router.post("/bulk-delete")
async def bulk_delete_prices(
    data: BulkDeleteRequest,
    current_user=Depends(require_permission("catalog.pricing.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _pricing_service(db, current_user)
    deleted_count = await service.bulk_delete(data.ids)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="ProductPrice", user_id=current_user.id,
        before={"ids": data.ids}, after={"deleted_count": deleted_count}, context=audit_context,
    )
    return {"deleted_count": deleted_count}


@router.get("/{price_id}", response_model=ProductPriceItem)
async def get_price(price_id: str, current_user=Depends(require_permission("catalog.products.view")), db: AsyncSession = Depends(get_db)):
    service = _pricing_service(db, current_user)
    price = await service.get_price(price_id)
    if not price:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price not found.")
    return price


@router.patch("/{price_id}", response_model=ProductPriceItem)
async def update_price(
    price_id: str,
    data: ProductPriceUpdateRequest,
    current_user=Depends(require_permission("catalog.pricing.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _pricing_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    price = await service.update_price(price_id, data, actor_id=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="price_change", module="catalog", entity="ProductPrice", entity_id=price.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return price


@router.delete("/{price_id}")
async def delete_price(
    price_id: str,
    current_user=Depends(require_permission("catalog.pricing.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _pricing_service(db, current_user)
    await service.delete_price(price_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="ProductPrice", entity_id=price_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Price deleted successfully."}
