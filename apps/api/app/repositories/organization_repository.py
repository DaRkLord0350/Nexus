from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization


class OrganizationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, organization_id: str) -> Organization | None:
        # Excludes soft-deleted organizations: without this, delete_organization()
        # (which only sets deleted_at, see OrganizationService) had no effect on
        # anything that reads the organization back through this path.
        statement = select(Organization).where(Organization.id == organization_id, Organization.deleted_at.is_(None))
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Organization | None:
        statement = select(Organization).where(Organization.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Organization | None:
        statement = select(Organization).where(Organization.name == name)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create(self, organization: Organization) -> Organization:
        self.session.add(organization)
        await self.session.commit()
        await self.session.refresh(organization)
        return organization
