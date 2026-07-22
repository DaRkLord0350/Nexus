from sqlalchemy.ext.asyncio import AsyncSession

from app.models.slug_redirect import SlugRedirect
from app.repositories.slug_redirect_repository import SlugRedirectRepository


class SlugRedirectService:
    """Shared by Category/Brand/Product/Collection services to log a redirect
    whenever a slug changes, so old links can be 301'd instead of 404'ing."""

    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.repo = SlugRedirectRepository(session, organization_id, is_superuser)

    async def record(self, entity_type: str, old_slug: str, new_slug: str) -> None:
        if old_slug == new_slug:
            return
        await self.repo.create(SlugRedirect(entity_type=entity_type, old_slug=old_slug, new_slug=new_slug))

    async def resolve(self, entity_type: str, slug: str) -> str | None:
        return await self.repo.resolve(entity_type, slug)

    async def list_for_entity_type(self, entity_type: str, limit: int = 100, offset: int = 0) -> list[SlugRedirect]:
        return await self.repo.list_for_entity_type(entity_type, limit, offset)
