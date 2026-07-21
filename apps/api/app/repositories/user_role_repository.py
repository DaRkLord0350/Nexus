from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_role import UserRole
from app.models.role import Role
from app.repositories.base_repository import BaseRepository


class UserRoleRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def get_by_user_and_role(self, user_id: str, role_id: str) -> UserRole | None:
        statement = select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
        statement = self._apply_tenant_filter(statement, UserRole)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: str) -> list[UserRole]:
        statement = select(UserRole).where(UserRole.user_id == user_id)
        statement = self._apply_tenant_filter(statement, UserRole)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def assign(self, user_id: str, role: Role) -> UserRole:
        user_role = UserRole(user_id=user_id, role_id=role.id, organization_id=role.organization_id)
        self.session.add(user_role)
        await self.session.commit()
        await self.session.refresh(user_role)
        return user_role

    async def unassign(self, user_id: str, role_id: str) -> None:
        statement = delete(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
        statement = self._apply_tenant_filter(statement, UserRole)
        await self.session.execute(statement)
        await self.session.commit()
