from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag
from app.repositories.tag_repository import TagRepository
from app.utils.text import slugify


class TagService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = TagRepository(session, organization_id, is_superuser)

    async def _ensure_unique_slug(self, slug: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_slug(slug)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A tag with that slug already exists.")

    async def create_tag(self, data) -> Tag:
        slug = slugify(data.slug or data.name, fallback="tag")
        await self._ensure_unique_slug(slug)
        return await self.repo.create(Tag(name=data.name, slug=slug))

    async def get_or_create_by_names(self, names: list[str]) -> list[Tag]:
        """Used by ProductService when tagging a product with free-text names."""
        tags: list[Tag] = []
        for raw_name in names:
            name = raw_name.strip()
            if not name:
                continue
            slug = slugify(name, fallback="tag")
            existing = await self.repo.get_by_slug(slug)
            if existing:
                tags.append(existing)
            else:
                tags.append(await self.repo.create(Tag(name=name, slug=slug)))
        return tags

    async def update_tag(self, tag_id: str, data) -> Tag:
        tag = await self.repo.get_by_id(tag_id)
        if not tag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found.")

        if data.slug is not None:
            new_slug = slugify(data.slug, fallback="tag")
            await self._ensure_unique_slug(new_slug, exclude_id=tag.id)
            tag.slug = new_slug
        elif data.name is not None:
            new_slug = slugify(data.name, fallback="tag")
            await self._ensure_unique_slug(new_slug, exclude_id=tag.id)
            tag.slug = new_slug

        if data.name is not None:
            tag.name = data.name

        return await self.repo.save(tag)

    async def delete_tag(self, tag_id: str) -> None:
        tag = await self.repo.get_by_id(tag_id)
        if not tag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found.")
        await self.repo.soft_delete(tag_id)

    async def get_tag(self, tag_id: str) -> Tag | None:
        return await self.repo.get_by_id(tag_id)

    async def list_tags(self, q: str | None = None, limit: int = 100, offset: int = 0) -> tuple[list[Tag], int]:
        items = await self.repo.list(q, limit, offset)
        total = await self.repo.count(q)
        return items, total
