from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.schemas.shipping_provider import (
    ShippingProviderCreateRequest,
    ShippingProviderListResponse,
    ShippingProviderRead,
    ShippingProviderUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.shipping_provider_service import ShippingProviderService

router = APIRouter(prefix="/providers", tags=["shipping-providers"])


def _provider_service(db: AsyncSession, current_user) -> ShippingProviderService:
    return ShippingProviderService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=ShippingProviderListResponse)
async def list_shipping_providers(
    is_active: bool | None = Query(None),
    provider_type: str | None = Query(None),
    sort_by: str = Query("priority"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("shipping.providers.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _provider_service(db, current_user)
    items, total = await service.list_providers(is_active, provider_type, sort_by, sort_order, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=ShippingProviderRead, status_code=status.HTTP_201_CREATED)
async def create_shipping_provider(
    data: ShippingProviderCreateRequest,
    current_user=Depends(require_permission("shipping.providers.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _provider_service(db, current_user)
    provider = await service.create_provider(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="shipping", entity="ShippingProvider", entity_id=provider.id,
        user_id=current_user.id, after={"code": provider.code, "provider_type": provider.provider_type}, context=audit_context,
    )
    return provider


@router.get("/{provider_id}", response_model=ShippingProviderRead)
async def get_shipping_provider(provider_id: str, current_user=Depends(require_permission("shipping.providers.view")), db: AsyncSession = Depends(get_db)):
    service = _provider_service(db, current_user)
    provider = await service.get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipping provider not found.")
    return provider


@router.patch("/{provider_id}", response_model=ShippingProviderRead)
async def update_shipping_provider(
    provider_id: str,
    data: ShippingProviderUpdateRequest,
    current_user=Depends(require_permission("shipping.providers.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _provider_service(db, current_user)
    changes = data.model_dump(exclude_unset=True, exclude={"credentials"})
    provider = await service.update_provider(provider_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="shipping", entity="ShippingProvider", entity_id=provider.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return provider


@router.delete("/{provider_id}")
async def delete_shipping_provider(
    provider_id: str,
    current_user=Depends(require_permission("shipping.providers.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _provider_service(db, current_user)
    await service.delete_provider(provider_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="shipping", entity="ShippingProvider", entity_id=provider_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Shipping provider deleted successfully."}
