from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_type import ProductType
from app.repositories.attribute_repository import AttributeRepository
from app.repositories.product_type_repository import ProductTypeRepository
from app.utils.text import slugify


class ProductTypeService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = ProductTypeRepository(session, organization_id, is_superuser)
        self.attribute_repo = AttributeRepository(session, organization_id, is_superuser)

    async def _ensure_unique_slug(self, slug: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_slug(slug)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A product type with that slug already exists.")

    async def create_product_type(self, data, created_by: str | None = None) -> ProductType:
        slug = slugify(data.slug or data.name, fallback="product-type")
        await self._ensure_unique_slug(slug)
        return await self.repo.create(ProductType(name=data.name, slug=slug, description=data.description, is_active=data.is_active, created_by=created_by))

    async def update_product_type(self, product_type_id: str, data) -> ProductType:
        product_type = await self.repo.get_by_id(product_type_id)
        if not product_type:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product type not found.")

        if data.slug is not None:
            new_slug = slugify(data.slug, fallback="product-type")
            await self._ensure_unique_slug(new_slug, exclude_id=product_type.id)
            product_type.slug = new_slug
        elif data.name is not None:
            new_slug = slugify(data.name, fallback="product-type")
            await self._ensure_unique_slug(new_slug, exclude_id=product_type.id)
            product_type.slug = new_slug

        changes = data.model_dump(exclude_unset=True, exclude={"slug"})
        for field, value in changes.items():
            setattr(product_type, field, value)

        return await self.repo.save(product_type)

    async def delete_product_type(self, product_type_id: str) -> None:
        product_type = await self.repo.get_by_id(product_type_id)
        if not product_type:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product type not found.")
        await self.repo.soft_delete(product_type_id)

    async def get_product_type(self, product_type_id: str) -> ProductType | None:
        return await self.repo.get_by_id(product_type_id)

    async def list_product_types(self, is_active: bool | None = None, q: str | None = None, limit: int = 100, offset: int = 0) -> tuple[list[ProductType], int]:
        items = await self.repo.list(is_active, q, limit, offset)
        total = await self.repo.count(is_active, q)
        return items, total

    async def set_attributes(self, product_type_id: str, configs: list) -> None:
        if not await self.repo.get_by_id(product_type_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product type not found.")
        for config in configs:
            if not await self.attribute_repo.get_by_id(config.attribute_id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Attribute {config.attribute_id} not found.")
        await self.repo.set_attributes(product_type_id, [c.model_dump() for c in configs])

    async def get_attributes(self, product_type_id: str) -> list[dict]:
        if not await self.repo.get_by_id(product_type_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product type not found.")
        rows = await self.repo.get_attributes(product_type_id)
        return [
            {
                "attribute_id": attribute.id,
                "name": attribute.name,
                "code": attribute.code,
                "is_required": link.is_required,
                "sort_order": link.sort_order,
            }
            for attribute, link in rows
        ]
