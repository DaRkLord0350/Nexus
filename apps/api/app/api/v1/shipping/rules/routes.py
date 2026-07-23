from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.schemas.shipping_rule import (
    ShippingRuleCreateRequest,
    ShippingRuleEvaluateRequest,
    ShippingRuleEvaluateResponse,
    ShippingRuleListResponse,
    ShippingRuleRead,
    ShippingRuleUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.shipping_rule_service import ShippingRuleService

router = APIRouter(prefix="/rules", tags=["shipping-rules"])


def _rule_service(db: AsyncSession, current_user) -> ShippingRuleService:
    return ShippingRuleService(db, current_user.organization_id, current_user.is_superuser)


@router.post("/evaluate", response_model=ShippingRuleEvaluateResponse)
async def evaluate_shipping_rules(
    data: ShippingRuleEvaluateRequest,
    current_user=Depends(require_permission("shipping.rules.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _rule_service(db, current_user)
    return await service.evaluate(data)


@router.get("/", response_model=ShippingRuleListResponse)
async def list_shipping_rules(
    is_active: bool | None = Query(None),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("shipping.rules.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _rule_service(db, current_user)
    items, total = await service.list_rules(is_active, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=ShippingRuleRead, status_code=status.HTTP_201_CREATED)
async def create_shipping_rule(
    data: ShippingRuleCreateRequest,
    current_user=Depends(require_permission("shipping.rules.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _rule_service(db, current_user)
    rule = await service.create_rule(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="shipping", entity="ShippingRule", entity_id=rule.id,
        user_id=current_user.id, after={"name": rule.name}, context=audit_context,
    )
    return rule


@router.get("/{rule_id}", response_model=ShippingRuleRead)
async def get_shipping_rule(rule_id: str, current_user=Depends(require_permission("shipping.rules.view")), db: AsyncSession = Depends(get_db)):
    service = _rule_service(db, current_user)
    rule = await service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipping rule not found.")
    return rule


@router.patch("/{rule_id}", response_model=ShippingRuleRead)
async def update_shipping_rule(
    rule_id: str,
    data: ShippingRuleUpdateRequest,
    current_user=Depends(require_permission("shipping.rules.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _rule_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    rule = await service.update_rule(rule_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="shipping", entity="ShippingRule", entity_id=rule.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return rule


@router.delete("/{rule_id}")
async def delete_shipping_rule(
    rule_id: str,
    current_user=Depends(require_permission("shipping.rules.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _rule_service(db, current_user)
    await service.delete_rule(rule_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="shipping", entity="ShippingRule", entity_id=rule_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Shipping rule deleted successfully."}
