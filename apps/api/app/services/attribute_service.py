from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attribute import Attribute, AttributeInputType
from app.models.attribute_value import AttributeValue
from app.repositories.attribute_repository import AttributeRepository
from app.repositories.attribute_value_repository import AttributeValueRepository
from app.utils.text import slugify


class AttributeService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.attribute_repo = AttributeRepository(session, organization_id, is_superuser)
        self.value_repo = AttributeValueRepository(session, organization_id, is_superuser)

    # ------------------------------------------------------------------
    # Attributes
    # ------------------------------------------------------------------
    async def _ensure_unique_code(self, code: str, exclude_id: str | None = None) -> None:
        existing = await self.attribute_repo.get_by_code(code)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An attribute with that code already exists.")

    async def create_attribute(self, data, created_by: str | None = None) -> Attribute:
        code = slugify(data.code or data.name, fallback="attribute")
        await self._ensure_unique_code(code)
        attribute = Attribute(
            name=data.name,
            code=code,
            input_type=AttributeInputType(data.input_type.value),
            is_variant_attribute=data.is_variant_attribute,
            sort_order=data.sort_order,
            is_active=data.is_active,
            created_by=created_by,
        )
        return await self.attribute_repo.create(attribute)

    async def update_attribute(self, attribute_id: str, data) -> Attribute:
        attribute = await self.attribute_repo.get_by_id(attribute_id)
        if not attribute:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attribute not found.")

        if data.code is not None:
            new_code = slugify(data.code, fallback="attribute")
            await self._ensure_unique_code(new_code, exclude_id=attribute.id)
            attribute.code = new_code
        elif data.name is not None:
            new_code = slugify(data.name, fallback="attribute")
            await self._ensure_unique_code(new_code, exclude_id=attribute.id)
            attribute.code = new_code

        changes = data.model_dump(exclude_unset=True, exclude={"code"})
        for field, value in changes.items():
            if field == "input_type" and value is not None:
                value = AttributeInputType(value.value if hasattr(value, "value") else value)
            setattr(attribute, field, value)

        return await self.attribute_repo.save(attribute)

    async def delete_attribute(self, attribute_id: str) -> None:
        attribute = await self.attribute_repo.get_by_id(attribute_id)
        if not attribute:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attribute not found.")
        await self.value_repo.soft_delete_for_attribute(attribute_id)
        await self.attribute_repo.soft_delete(attribute_id)

    async def bulk_delete_attributes(self, attribute_ids: list[str]) -> int:
        for attribute_id in attribute_ids:
            await self.value_repo.soft_delete_for_attribute(attribute_id)
        return await self.attribute_repo.bulk_soft_delete(attribute_ids)

    async def get_attribute(self, attribute_id: str) -> Attribute | None:
        return await self.attribute_repo.get_by_id(attribute_id)

    async def list_attributes(
        self,
        is_active: bool | None = None,
        is_variant_attribute: bool | None = None,
        q: str | None = None,
        sort_by: str = "sort_order",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Attribute], int]:
        items = await self.attribute_repo.list(is_active, is_variant_attribute, q, sort_by, sort_order, limit, offset)
        total = await self.attribute_repo.count(is_active, is_variant_attribute, q)
        return items, total

    # ------------------------------------------------------------------
    # Attribute values
    # ------------------------------------------------------------------
    async def _ensure_unique_value_slug(self, attribute_id: str, slug: str, exclude_id: str | None = None) -> None:
        existing = await self.value_repo.get_by_slug(attribute_id, slug)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A value with that slug already exists for this attribute.")

    async def create_value(self, attribute_id: str, data) -> AttributeValue:
        attribute = await self.attribute_repo.get_by_id(attribute_id)
        if not attribute:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attribute not found.")

        slug = slugify(data.slug or data.value, fallback="value")
        await self._ensure_unique_value_slug(attribute_id, slug)

        value = AttributeValue(
            attribute_id=attribute_id,
            value=data.value,
            slug=slug,
            color_hex=data.color_hex,
            sort_order=data.sort_order,
            is_active=data.is_active,
        )
        return await self.value_repo.create(value)

    async def update_value(self, attribute_id: str, value_id: str, data) -> AttributeValue:
        value = await self.value_repo.get_by_id(value_id)
        if not value or value.attribute_id != attribute_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attribute value not found.")

        if data.slug is not None:
            new_slug = slugify(data.slug, fallback="value")
            await self._ensure_unique_value_slug(attribute_id, new_slug, exclude_id=value.id)
            value.slug = new_slug
        elif data.value is not None:
            new_slug = slugify(data.value, fallback="value")
            await self._ensure_unique_value_slug(attribute_id, new_slug, exclude_id=value.id)
            value.slug = new_slug

        changes = data.model_dump(exclude_unset=True, exclude={"slug"})
        for field, field_value in changes.items():
            setattr(value, field, field_value)

        return await self.value_repo.save(value)

    async def delete_value(self, attribute_id: str, value_id: str) -> None:
        value = await self.value_repo.get_by_id(value_id)
        if not value or value.attribute_id != attribute_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attribute value not found.")
        await self.value_repo.soft_delete(value_id)

    async def bulk_delete_values(self, value_ids: list[str]) -> int:
        return await self.value_repo.bulk_soft_delete(value_ids)

    async def list_values(self, attribute_id: str, is_active: bool | None = None) -> list[AttributeValue]:
        attribute = await self.attribute_repo.get_by_id(attribute_id)
        if not attribute:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attribute not found.")
        return await self.value_repo.list_for_attribute(attribute_id, is_active)
