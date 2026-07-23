from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole


class PermissionService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser

    async def has_permission(self, user_id: str, permission_code: str) -> bool:
        if self.is_superuser:
            return True

        # A user can legitimately hold multiple roles that each grant the same
        # permission (e.g. both "Owner" and "Admin"), so this must be an
        # existence check rather than assume the join yields at most one row.
        subquery = (
            select(Permission.id)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id, Permission.code == permission_code)
        )

        if self.organization_id:
            subquery = subquery.where(Permission.organization_id == self.organization_id)

        result = await self.session.execute(select(subquery.exists()))
        return bool(result.scalar())

    async def get_user_permissions(self, user_id: str) -> list[str]:
        if self.is_superuser:
            statement = select(Permission.code).distinct()
            if self.organization_id:
                statement = statement.where(Permission.organization_id == self.organization_id)
            result = await self.session.execute(statement)
            return [row[0] for row in result.all()]

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

    async def list_user_ids_with_permission(self, permission_code: str) -> list[str]:
        """Used for notification fan-out (e.g. low-stock alerts) — resolves
        which users in this organization hold a given permission, so
        recipients can be targeted by role instead of notifying everyone."""
        statement = (
            select(User.id)
            .distinct()
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .join(RolePermission, RolePermission.role_id == Role.id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(Permission.code == permission_code, User.is_active.is_(True))
        )

        if self.organization_id:
            statement = statement.where(User.organization_id == self.organization_id, Permission.organization_id == self.organization_id)

        result = await self.session.execute(statement)
        return [row[0] for row in result.all()]
