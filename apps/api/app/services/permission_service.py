from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user_role import UserRole


class PermissionService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser

    async def has_permission(self, user_id: str, permission_code: str) -> bool:
        if self.is_superuser:
            return True

        statement = (
            select(Permission.code)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id, Permission.code == permission_code)
        )

        if self.organization_id:
            statement = statement.where(Permission.organization_id == self.organization_id)

        result = await self.session.execute(statement)
        return result.scalar_one_or_none() is not None

    async def get_user_permissions(self, user_id: str) -> list[str]:
        statement = (
            select(Permission.code)
            .distinct()
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )

        if self.organization_id:
            statement = statement.where(Permission.organization_id == self.organization_id)

        result = await self.session.execute(statement)
        return [row[0] for row in result.all()]

    async def get_user_roles(self, user_id: str) -> list[str]:
        statement = (
            select(Role.name)
            .distinct()
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )

        if self.organization_id:
            statement = statement.where(Role.organization_id == self.organization_id)

        result = await self.session.execute(statement)
        return [row[0] for row in result.all()]
