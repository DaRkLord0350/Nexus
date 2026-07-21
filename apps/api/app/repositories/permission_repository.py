from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Permission
from app.repositories.base_repository import BaseRepository


class PermissionRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def get_by_code(self, code: str) -> Permission | None:
        statement = select(Permission).where(Permission.code == code)
        statement = self._apply_tenant_filter(statement, Permission)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create(self, permission: Permission) -> Permission:
        self._add_tenant_on_create(permission)
        self.session.add(permission)
        await self.session.commit()
        await self.session.refresh(permission)
        return permission

    async def list(self) -> list[Permission]:
        statement = select(Permission)
        statement = self._apply_tenant_filter(statement, Permission)
        result = await self.session.execute(statement)
        return result.scalars().all()
