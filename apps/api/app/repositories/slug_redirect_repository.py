from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.slug_redirect import SlugRedirect
from app.repositories.base_repository import BaseRepository


class SlugRedirectRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, redirect: SlugRedirect) -> SlugRedirect:
        self._add_tenant_on_create(redirect)
        self.session.add(redirect)
        await self.session.commit()
        await self.session.refresh(redirect)
        return redirect

    async def resolve(self, entity_type: str, old_slug: str) -> str | None:
        """Follows a redirect chain (A->B->C) to the final current slug."""
        seen: set[str] = set()
        current_slug = old_slug
        latest_new_slug: str | None = None
        while current_slug not in seen:
            seen.add(current_slug)
            statement = select(SlugRedirect).where(SlugRedirect.entity_type == entity_type, SlugRedirect.old_slug == current_slug)
            statement = self._apply_tenant_filter(statement, SlugRedirect)
            result = await self.session.execute(statement)
            redirect = result.scalars().first()
            if not redirect:
                break
            latest_new_slug = redirect.new_slug
            current_slug = redirect.new_slug
        return latest_new_slug

    async def list_for_entity_type(self, entity_type: str, limit: int = 100, offset: int = 0) -> list[SlugRedirect]:
        statement = (
            select(SlugRedirect)
            .where(SlugRedirect.entity_type == entity_type)
            .order_by(SlugRedirect.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        statement = self._apply_tenant_filter(statement, SlugRedirect)
        result = await self.session.execute(statement)
        return result.scalars().all()
