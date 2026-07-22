from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_db, require_permission
from app.schemas.reorder_rule import (
    BulkDeleteRequest,
    ReorderRuleCreateRequest,
    ReorderRuleItem,
    ReorderRuleListResponse,
    ReorderRuleUpdateRequest,
)
from app.services.audit_service import AuditService
from app.services.reorder_rule_service import ReorderRuleService

router = APIRouter(prefix="/reorder-rules", tags=["inventory-reorder-rules"])


def _rule_service(db: AsyncSession, current_user) -> ReorderRuleService:
    return ReorderRuleService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=ReorderRuleListResponse)
async def list_reorder_rules(
    warehouse_id: str | None = Query(None),
    product_id: str | None = Query(None),
    is_active: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("inventory.reorder_rules.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _rule_service(db, current_user)
    items, total = await service.list_rules(warehouse_id, product_id, is_active, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=ReorderRuleItem, status_code=status.HTTP_201_CREATED)
async def create_reorder_rule(
    data: ReorderRuleCreateRequest,
    current_user=Depends(require_permission("inventory.reorder_rules.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _rule_service(db, current_user)
    rule = await service.create_rule(data)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="inventory", entity="ReorderRule", entity_id=rule.id,
        user_id=current_user.id, after={"product_id": rule.product_id, "warehouse_id": rule.warehouse_id}, context=audit_context,
    )
    return rule


@router.post("/bulk-delete")
async def bulk_delete_reorder_rules(
    data: BulkDeleteRequest,
    current_user=Depends(require_permission("inventory.reorder_rules.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _rule_service(db, current_user)
    deleted_count = await service.bulk_delete(data.ids)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="inventory", entity="ReorderRule", user_id=current_user.id,
        before={"ids": data.ids}, after={"deleted_count": deleted_count}, context=audit_context,
    )
    return {"deleted_count": deleted_count}


@router.get("/{rule_id}", response_model=ReorderRuleItem)
async def get_reorder_rule(rule_id: str, current_user=Depends(require_permission("inventory.reorder_rules.view")), db: AsyncSession = Depends(get_db)):
    service = _rule_service(db, current_user)
    rule = await service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reorder rule not found.")
    return rule


@router.patch("/{rule_id}", response_model=ReorderRuleItem)
async def update_reorder_rule(
    rule_id: str,
    data: ReorderRuleUpdateRequest,
    current_user=Depends(require_permission("inventory.reorder_rules.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _rule_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    rule = await service.update_rule(rule_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="inventory", entity="ReorderRule", entity_id=rule.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return rule


@router.delete("/{rule_id}")
async def delete_reorder_rule(
    rule_id: str,
    current_user=Depends(require_permission("inventory.reorder_rules.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _rule_service(db, current_user)
    await service.delete_rule(rule_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="inventory", entity="ReorderRule", entity_id=rule_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Reorder rule deleted successfully."}
