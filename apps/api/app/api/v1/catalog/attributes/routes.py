from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_current_active_user, get_db, require_permission
from app.schemas.attribute import (
    AttributeCreateRequest,
    AttributeItem,
    AttributeListResponse,
    AttributeUpdateRequest,
    AttributeValueCreateRequest,
    AttributeValueItem,
    AttributeValueUpdateRequest,
    BulkDeleteRequest,
)
from app.services.attribute_service import AttributeService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/attributes", tags=["catalog-attributes"])


def _attribute_service(db: AsyncSession, current_user) -> AttributeService:
    return AttributeService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/", response_model=AttributeListResponse)
async def list_attributes(
    is_active: bool | None = Query(None),
    is_variant_attribute: bool | None = Query(None),
    q: str | None = Query(None),
    sort_by: str = Query("sort_order"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(require_permission("catalog.attributes.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _attribute_service(db, current_user)
    items, total = await service.list_attributes(is_active, is_variant_attribute, q, sort_by, sort_order, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/", response_model=AttributeItem, status_code=status.HTTP_201_CREATED)
async def create_attribute(
    data: AttributeCreateRequest,
    current_user=Depends(require_permission("catalog.attributes.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _attribute_service(db, current_user)
    attribute = await service.create_attribute(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="catalog", entity="Attribute", entity_id=attribute.id,
        user_id=current_user.id, after={"name": attribute.name, "code": attribute.code}, context=audit_context,
    )
    return attribute


@router.post("/bulk-delete")
async def bulk_delete_attributes(
    data: BulkDeleteRequest,
    current_user=Depends(require_permission("catalog.attributes.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _attribute_service(db, current_user)
    deleted_count = await service.bulk_delete_attributes(data.ids)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="Attribute", user_id=current_user.id,
        before={"ids": data.ids}, after={"deleted_count": deleted_count}, context=audit_context,
    )
    return {"deleted_count": deleted_count}


@router.get("/{attribute_id}", response_model=AttributeItem)
async def get_attribute(attribute_id: str, current_user=Depends(require_permission("catalog.attributes.view")), db: AsyncSession = Depends(get_db)):
    service = _attribute_service(db, current_user)
    attribute = await service.get_attribute(attribute_id)
    if not attribute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attribute not found.")
    return attribute


@router.patch("/{attribute_id}", response_model=AttributeItem)
async def update_attribute(
    attribute_id: str,
    data: AttributeUpdateRequest,
    current_user=Depends(require_permission("catalog.attributes.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _attribute_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    attribute = await service.update_attribute(attribute_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="Attribute", entity_id=attribute.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return attribute


@router.delete("/{attribute_id}")
async def delete_attribute(
    attribute_id: str,
    current_user=Depends(require_permission("catalog.attributes.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _attribute_service(db, current_user)
    await service.delete_attribute(attribute_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="Attribute", entity_id=attribute_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Attribute deleted successfully."}


@router.get("/{attribute_id}/values", response_model=list[AttributeValueItem])
async def list_attribute_values(
    attribute_id: str,
    is_active: bool | None = Query(None),
    current_user=Depends(require_permission("catalog.attributes.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _attribute_service(db, current_user)
    return await service.list_values(attribute_id, is_active)


@router.post("/{attribute_id}/values", response_model=AttributeValueItem, status_code=status.HTTP_201_CREATED)
async def create_attribute_value(
    attribute_id: str,
    data: AttributeValueCreateRequest,
    current_user=Depends(require_permission("catalog.attributes.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _attribute_service(db, current_user)
    value = await service.create_value(attribute_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="catalog", entity="AttributeValue", entity_id=value.id,
        user_id=current_user.id, after={"value": value.value, "attribute_id": attribute_id}, context=audit_context,
    )
    return value


@router.post("/values/bulk-delete")
async def bulk_delete_attribute_values(
    data: BulkDeleteRequest,
    current_user=Depends(require_permission("catalog.attributes.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _attribute_service(db, current_user)
    deleted_count = await service.bulk_delete_values(data.ids)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="AttributeValue", user_id=current_user.id,
        before={"ids": data.ids}, after={"deleted_count": deleted_count}, context=audit_context,
    )
    return {"deleted_count": deleted_count}


@router.patch("/{attribute_id}/values/{value_id}", response_model=AttributeValueItem)
async def update_attribute_value(
    attribute_id: str,
    value_id: str,
    data: AttributeValueUpdateRequest,
    current_user=Depends(require_permission("catalog.attributes.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _attribute_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    value = await service.update_value(attribute_id, value_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="AttributeValue", entity_id=value.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return value


@router.delete("/{attribute_id}/values/{value_id}")
async def delete_attribute_value(
    attribute_id: str,
    value_id: str,
    current_user=Depends(require_permission("catalog.attributes.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _attribute_service(db, current_user)
    await service.delete_value(attribute_id, value_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="AttributeValue", entity_id=value_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Attribute value deleted successfully."}
