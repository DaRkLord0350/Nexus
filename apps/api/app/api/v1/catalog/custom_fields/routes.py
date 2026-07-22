from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_current_active_user, get_db, require_permission
from app.models.custom_field_definition import CustomFieldEntityType as ModelCustomFieldEntityType
from app.schemas.custom_field import (
    CustomFieldDefinitionCreateRequest,
    CustomFieldDefinitionItem,
    CustomFieldDefinitionListResponse,
    CustomFieldDefinitionUpdateRequest,
    CustomFieldEntityType,
    CustomFieldValueItem,
    SetCustomFieldValuesRequest,
)
from app.services.audit_service import AuditService
from app.services.custom_field_service import CustomFieldService

router = APIRouter(prefix="/custom-fields", tags=["catalog-custom-fields"])


def _custom_field_service(db: AsyncSession, current_user) -> CustomFieldService:
    return CustomFieldService(db, current_user.organization_id, current_user.is_superuser)


@router.get("/definitions", response_model=CustomFieldDefinitionListResponse)
async def list_definitions(
    entity_type: CustomFieldEntityType = Query(...),
    is_active: bool | None = Query(None),
    current_user=Depends(require_permission("catalog.products.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _custom_field_service(db, current_user)
    items, total = await service.list_definitions(ModelCustomFieldEntityType(entity_type.value), is_active)
    return {"items": items, "total": total}


@router.post("/definitions", response_model=CustomFieldDefinitionItem, status_code=status.HTTP_201_CREATED)
async def create_definition(
    data: CustomFieldDefinitionCreateRequest,
    current_user=Depends(require_permission("catalog.custom_fields.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _custom_field_service(db, current_user)
    definition = await service.create_definition(data, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create", module="catalog", entity="CustomFieldDefinition", entity_id=definition.id,
        user_id=current_user.id, after={"name": definition.name, "key": definition.key, "entity_type": definition.entity_type.value}, context=audit_context,
    )
    return definition


@router.patch("/definitions/{definition_id}", response_model=CustomFieldDefinitionItem)
async def update_definition(
    definition_id: str,
    data: CustomFieldDefinitionUpdateRequest,
    current_user=Depends(require_permission("catalog.custom_fields.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _custom_field_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    definition = await service.update_definition(definition_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="CustomFieldDefinition", entity_id=definition.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return definition


@router.delete("/definitions/{definition_id}")
async def delete_definition(
    definition_id: str,
    current_user=Depends(require_permission("catalog.custom_fields.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _custom_field_service(db, current_user)
    await service.delete_definition(definition_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="CustomFieldDefinition", entity_id=definition_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Custom field deleted successfully."}


@router.get("/values", response_model=list[CustomFieldValueItem])
async def get_values(
    entity_type: CustomFieldEntityType = Query(...),
    entity_id: str = Query(...),
    current_user=Depends(require_permission("catalog.products.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _custom_field_service(db, current_user)
    return await service.get_values_for_entity(ModelCustomFieldEntityType(entity_type.value), entity_id)


@router.put("/values", response_model=list[CustomFieldValueItem])
async def set_values(
    data: SetCustomFieldValuesRequest,
    entity_type: CustomFieldEntityType = Query(...),
    entity_id: str = Query(...),
    current_user=Depends(require_permission("catalog.custom_fields.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _custom_field_service(db, current_user)
    result = await service.set_values_for_entity(ModelCustomFieldEntityType(entity_type.value), entity_id, data.values)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="CustomFieldValue", entity_id=entity_id,
        user_id=current_user.id, after={"entity_type": entity_type.value, "values": data.values}, context=audit_context,
    )
    return result
