from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_current_active_user, get_db, require_permission
from app.schemas.tax import (
    TaxCalculationResponse,
    TaxClassCreateRequest,
    TaxClassItem,
    TaxClassListResponse,
    TaxClassUpdateRequest,
    TaxRateCreateRequest,
    TaxRateItem,
    TaxRateUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.tax_service import TaxService

router = APIRouter(prefix="/taxes", tags=["catalog-tax"])


def _tax_service(db: AsyncSession, current_user) -> TaxService:
    return TaxService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/classes", response_model=TaxClassListResponse)
async def list_tax_classes(
    is_active: bool | None = Query(None),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("catalog.products.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _tax_service(db, current_user)
    items, total = await service.list_tax_classes(is_active, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/classes", response_model=TaxClassItem, status_code=status.HTTP_201_CREATED)
async def create_tax_class(
    data: TaxClassCreateRequest,
    current_user=Depends(require_permission("catalog.tax.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _tax_service(db, current_user)
    tax_class = await service.create_tax_class(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="catalog", entity="TaxClass", entity_id=tax_class.id,
        user_id=current_user.id, after={"name": tax_class.name, "code": tax_class.code}, context=audit_context,
    )
    return tax_class


@router.get("/classes/{tax_class_id}", response_model=TaxClassItem)
async def get_tax_class(tax_class_id: str, current_user=Depends(require_permission("catalog.products.view")), db: AsyncSession = Depends(get_db)):
    service = _tax_service(db, current_user)
    tax_class = await service.get_tax_class(tax_class_id)
    if not tax_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tax class not found.")
    return tax_class


@router.patch("/classes/{tax_class_id}", response_model=TaxClassItem)
async def update_tax_class(
    tax_class_id: str,
    data: TaxClassUpdateRequest,
    current_user=Depends(require_permission("catalog.tax.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _tax_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    tax_class = await service.update_tax_class(tax_class_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="TaxClass", entity_id=tax_class.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return tax_class


@router.delete("/classes/{tax_class_id}")
async def delete_tax_class(
    tax_class_id: str,
    current_user=Depends(require_permission("catalog.tax.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _tax_service(db, current_user)
    await service.delete_tax_class(tax_class_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="TaxClass", entity_id=tax_class_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Tax class deleted successfully."}


@router.get("/classes/{tax_class_id}/rates", response_model=list[TaxRateItem])
async def list_tax_rates(tax_class_id: str, current_user=Depends(require_permission("catalog.products.view")), db: AsyncSession = Depends(get_db)):
    service = _tax_service(db, current_user)
    return await service.list_tax_rates(tax_class_id)


@router.post("/classes/{tax_class_id}/rates", response_model=TaxRateItem, status_code=status.HTTP_201_CREATED)
async def create_tax_rate(
    tax_class_id: str,
    data: TaxRateCreateRequest,
    current_user=Depends(require_permission("catalog.tax.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _tax_service(db, current_user)
    tax_rate = await service.create_tax_rate(tax_class_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="catalog", entity="TaxRate", entity_id=tax_rate.id,
        user_id=current_user.id, after={"country": tax_rate.country, "rate": tax_rate.rate}, context=audit_context,
    )
    return tax_rate


@router.patch("/classes/{tax_class_id}/rates/{tax_rate_id}", response_model=TaxRateItem)
async def update_tax_rate(
    tax_class_id: str,
    tax_rate_id: str,
    data: TaxRateUpdateRequest,
    current_user=Depends(require_permission("catalog.tax.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _tax_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    tax_rate = await service.update_tax_rate(tax_class_id, tax_rate_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="TaxRate", entity_id=tax_rate.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return tax_rate


@router.delete("/classes/{tax_class_id}/rates/{tax_rate_id}")
async def delete_tax_rate(
    tax_class_id: str,
    tax_rate_id: str,
    current_user=Depends(require_permission("catalog.tax.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _tax_service(db, current_user)
    await service.delete_tax_rate(tax_class_id, tax_rate_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="TaxRate", entity_id=tax_rate_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Tax rate deleted successfully."}


@router.get("/calculate", response_model=TaxCalculationResponse)
async def calculate_tax(
    tax_class_id: str = Query(...),
    amount: float = Query(..., ge=0),
    country: str = Query(..., min_length=2, max_length=2),
    state: str | None = Query(None),
    current_user=Depends(require_permission("catalog.products.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _tax_service(db, current_user)
    return await service.calculate_tax(tax_class_id, amount, country, state)
