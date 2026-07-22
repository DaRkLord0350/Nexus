from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.custom_field_definition import CustomFieldDefinition, CustomFieldEntityType
from app.models.custom_field_value import CustomFieldValue
from app.repositories.base_repository import BaseRepository


class CustomFieldDefinitionRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, definition: CustomFieldDefinition) -> CustomFieldDefinition:
        self._add_tenant_on_create(definition)
        self.session.add(definition)
        await self.session.commit()
        await self.session.refresh(definition)
        return definition

    async def save(self, definition: CustomFieldDefinition) -> CustomFieldDefinition:
        self.session.add(definition)
        await self.session.commit()
        await self.session.refresh(definition)
        return definition

    async def get_by_id(self, definition_id: str) -> CustomFieldDefinition | None:
        statement = select(CustomFieldDefinition).where(CustomFieldDefinition.id == definition_id)
        statement = self._apply_tenant_filter(statement, CustomFieldDefinition)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_key(self, entity_type: CustomFieldEntityType, key: str) -> CustomFieldDefinition | None:
        statement = select(CustomFieldDefinition).where(
            CustomFieldDefinition.entity_type == entity_type, CustomFieldDefinition.key == key
        )
        statement = self._apply_tenant_filter(statement, CustomFieldDefinition)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_entity_type(self, entity_type: CustomFieldEntityType, is_active: bool | None = None) -> list[CustomFieldDefinition]:
        statement = select(CustomFieldDefinition).where(CustomFieldDefinition.entity_type == entity_type).order_by(CustomFieldDefinition.sort_order.asc())
        if is_active is not None:
            statement = statement.where(CustomFieldDefinition.is_active == is_active)
        statement = self._apply_tenant_filter(statement, CustomFieldDefinition)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count_for_entity_type(self, entity_type: CustomFieldEntityType) -> int:
        statement = select(func.count(CustomFieldDefinition.id)).where(CustomFieldDefinition.entity_type == entity_type)
        statement = self._apply_tenant_filter(statement, CustomFieldDefinition)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def soft_delete(self, definition_id: str) -> None:
        statement = update(CustomFieldDefinition).where(CustomFieldDefinition.id == definition_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, CustomFieldDefinition)
        await self.session.execute(statement)
        await self.session.commit()


class CustomFieldValueRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def get_for_entity(self, entity_type: str, entity_id: str) -> list[CustomFieldValue]:
        statement = select(CustomFieldValue).where(
            CustomFieldValue.entity_type == entity_type, CustomFieldValue.entity_id == entity_id
        )
        statement = self._apply_tenant_filter(statement, CustomFieldValue)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def upsert(self, definition_id: str, entity_type: str, entity_id: str, value) -> CustomFieldValue:
        statement = select(CustomFieldValue).where(
            CustomFieldValue.definition_id == definition_id, CustomFieldValue.entity_id == entity_id
        )
        statement = self._apply_tenant_filter(statement, CustomFieldValue)
        result = await self.session.execute(statement)
        existing = result.scalar_one_or_none()

        if existing:
            existing.value = value
            self.session.add(existing)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        created = CustomFieldValue(definition_id=definition_id, entity_type=entity_type, entity_id=entity_id, value=value)
        self._add_tenant_on_create(created)
        self.session.add(created)
        await self.session.commit()
        await self.session.refresh(created)
        return created
