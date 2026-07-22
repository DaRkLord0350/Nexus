from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.custom_field_definition import CustomFieldDefinition, CustomFieldEntityType, CustomFieldType
from app.repositories.custom_field_repository import CustomFieldDefinitionRepository, CustomFieldValueRepository
from app.utils.text import slugify


class CustomFieldService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.definition_repo = CustomFieldDefinitionRepository(session, organization_id, is_superuser)
        self.value_repo = CustomFieldValueRepository(session, organization_id, is_superuser)

    # ------------------------------------------------------------------
    # Definitions
    # ------------------------------------------------------------------
    async def _ensure_unique_key(self, entity_type: CustomFieldEntityType, key: str, exclude_id: str | None = None) -> None:
        existing = await self.definition_repo.get_by_key(entity_type, key)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A custom field with that key already exists for this entity type.")

    async def create_definition(self, data, created_by: str | None = None) -> CustomFieldDefinition:
        entity_type = CustomFieldEntityType(data.entity_type.value)
        key = slugify(data.key or data.name, fallback="field").replace("-", "_")
        await self._ensure_unique_key(entity_type, key)

        if data.field_type.value == "select" and not data.options:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select fields require at least one option.")

        definition = CustomFieldDefinition(
            entity_type=entity_type,
            name=data.name,
            key=key,
            field_type=CustomFieldType(data.field_type.value),
            options=data.options,
            is_required=data.is_required,
            sort_order=data.sort_order,
            is_active=data.is_active,
            created_by=created_by,
        )
        return await self.definition_repo.create(definition)

    async def update_definition(self, definition_id: str, data) -> CustomFieldDefinition:
        definition = await self.definition_repo.get_by_id(definition_id)
        if not definition:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom field not found.")

        changes = data.model_dump(exclude_unset=True, exclude={"field_type"})
        for field, value in changes.items():
            setattr(definition, field, value)
        if data.field_type is not None:
            definition.field_type = CustomFieldType(data.field_type.value)

        if definition.field_type == CustomFieldType.select and not definition.options:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select fields require at least one option.")

        return await self.definition_repo.save(definition)

    async def delete_definition(self, definition_id: str) -> None:
        definition = await self.definition_repo.get_by_id(definition_id)
        if not definition:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom field not found.")
        await self.definition_repo.soft_delete(definition_id)

    async def list_definitions(self, entity_type: CustomFieldEntityType | str, is_active: bool | None = None) -> tuple[list[CustomFieldDefinition], int]:
        entity_type = CustomFieldEntityType(entity_type)
        items = await self.definition_repo.list_for_entity_type(entity_type, is_active)
        total = await self.definition_repo.count_for_entity_type(entity_type)
        return items, total

    # ------------------------------------------------------------------
    # Values
    # ------------------------------------------------------------------
    def _validate_value(self, definition: CustomFieldDefinition, value) -> None:
        if value is None:
            return
        if definition.field_type == CustomFieldType.number and not isinstance(value, (int, float)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"'{definition.name}' must be a number.")
        if definition.field_type == CustomFieldType.boolean and not isinstance(value, bool):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"'{definition.name}' must be true or false.")
        if definition.field_type == CustomFieldType.select and value not in (definition.options or []):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"'{definition.name}' must be one of {definition.options}.")

    async def get_values_for_entity(self, entity_type: CustomFieldEntityType | str, entity_id: str) -> list[dict]:
        entity_type = CustomFieldEntityType(entity_type)
        definitions = await self.definition_repo.list_for_entity_type(entity_type, is_active=True)
        values = await self.value_repo.get_for_entity(entity_type.value, entity_id)
        values_by_definition = {v.definition_id: v.value for v in values}
        return [
            {
                "definition_id": d.id,
                "key": d.key,
                "name": d.name,
                "field_type": d.field_type,
                "value": values_by_definition.get(d.id),
            }
            for d in definitions
        ]

    async def set_values_for_entity(self, entity_type: CustomFieldEntityType | str, entity_id: str, values: dict) -> list[dict]:
        entity_type = CustomFieldEntityType(entity_type)
        definitions = await self.definition_repo.list_for_entity_type(entity_type, is_active=True)
        definitions_by_key = {d.key: d for d in definitions}

        for key, value in values.items():
            definition = definitions_by_key.get(key)
            if not definition:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown custom field '{key}' for {entity_type.value}.")
            self._validate_value(definition, value)
            await self.value_repo.upsert(definition.id, entity_type.value, entity_id, value)

        return await self.get_values_for_entity(entity_type, entity_id)
