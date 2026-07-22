from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand import Brand, BrandStatus
from app.repositories.brand_repository import BrandRepository
from app.services.slug_redirect_service import SlugRedirectService
from app.utils.text import slugify


class BrandService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = BrandRepository(session, organization_id, is_superuser)
        self.slug_redirect_service = SlugRedirectService(session, organization_id, is_superuser)

    async def _ensure_unique_slug(self, slug: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_slug(slug)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A brand with that slug already exists.")

    async def create_brand(self, data, created_by: str | None = None) -> Brand:
        slug = slugify(data.slug or data.name, fallback="brand")
        await self._ensure_unique_slug(slug)
        brand = Brand(
            name=data.name,
            slug=slug,
            description=data.description,
            logo_url=data.logo_url,
            website=data.website,
            is_featured=data.is_featured,
            status=BrandStatus(data.status.value),
            seo_title=data.seo_title,
            seo_description=data.seo_description,
            seo_keywords=data.seo_keywords,
            og_image_url=data.og_image_url,
            canonical_url=data.canonical_url,
            no_index=data.no_index,
            created_by=created_by,
        )
        return await self.repo.create(brand)

    async def update_brand(self, brand_id: str, data) -> Brand:
        brand = await self.repo.get_by_id(brand_id)
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found.")

        old_slug = brand.slug
        new_slug = brand.slug
        if data.slug is not None:
            new_slug = slugify(data.slug, fallback="brand")
            await self._ensure_unique_slug(new_slug, exclude_id=brand.id)
        elif data.name is not None:
            new_slug = slugify(data.name, fallback="brand")
            await self._ensure_unique_slug(new_slug, exclude_id=brand.id)

        if new_slug != old_slug:
            await self.slug_redirect_service.record("brand", old_slug, new_slug)
            brand.slug = new_slug

        changes = data.model_dump(exclude_unset=True, exclude={"slug"})
        for field, value in changes.items():
            if field == "status" and value is not None:
                value = BrandStatus(value.value if hasattr(value, "value") else value)
            setattr(brand, field, value)

        return await self.repo.save(brand)

    async def delete_brand(self, brand_id: str) -> None:
        brand = await self.repo.get_by_id(brand_id)
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found.")
        await self.repo.soft_delete(brand_id)

    async def bulk_delete(self, brand_ids: list[str]) -> int:
        return await self.repo.bulk_soft_delete(brand_ids)

    async def restore_brand(self, brand_id: str) -> Brand:
        brand = await self.repo.get_by_id_including_deleted(brand_id)
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found.")
        if brand.deleted_at is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Brand is not deleted.")
        return await self.repo.restore(brand_id)

    async def get_brand(self, brand_id: str) -> Brand | None:
        return await self.repo.get_by_id(brand_id)

    async def get_by_slug(self, slug: str) -> Brand | None:
        return await self.repo.get_by_slug(slug)

    async def list_brands(
        self,
        status_filter: BrandStatus | None = None,
        is_featured: bool | None = None,
        q: str | None = None,
        sort_by: str = "name",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Brand], int]:
        items = await self.repo.list(status_filter, is_featured, q, sort_by, sort_order, limit, offset)
        total = await self.repo.count(status_filter, is_featured, q)
        return items, total
