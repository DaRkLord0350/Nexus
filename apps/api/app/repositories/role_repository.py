from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.repositories.base_repository import BaseRepository


class RoleRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def get_by_id(self, role_id: str) -> Role | None:
        statement = select(Role).options(selectinload(Role.permissions).selectinload(RolePermission.permission)).where(Role.id == role_id)
        statement = self._apply_tenant_filter(statement, Role)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Role | None:
        statement = select(Role).options(selectinload(Role.permissions).selectinload(RolePermission.permission)).where(Role.name == name)
        statement = self._apply_tenant_filter(statement, Role)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_permission_ids(self, role_id: str) -> set[str]:
        statement = select(RolePermission.permission_id).where(RolePermission.role_id == role_id)
        result = await self.session.execute(statement)
        return {row[0] for row in result.all()}

    async def list(self) -> list[Role]:
        statement = select(Role).options(selectinload(Role.permissions).selectinload(RolePermission.permission))
        statement = self._apply_tenant_filter(statement, Role)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def create(self, role: Role) -> Role:
        self._add_tenant_on_create(role)
        self.session.add(role)
        await self.session.commit()
        await self.session.refresh(role)
        return role

    async def delete(self, role_id: str) -> None:
        statement = delete(Role).where(Role.id == role_id)
        statement = self._apply_tenant_filter(statement, Role)
        await self.session.execute(statement)
        await self.session.commit()

    async def add_permission(self, role: Role, permission: Permission) -> RolePermission:
        role_permission = RolePermission(
            role_id=role.id,
            permission_id=permission.id,
            organization_id=role.organization_id,
        )
        self.session.add(role_permission)
        await self.session.commit()
        await self.session.refresh(role_permission)
        return role_permission

    async def remove_permission(self, role_id: str, permission_id: str) -> None:
        statement = delete(RolePermission).where(RolePermission.role_id == role_id, RolePermission.permission_id == permission_id)
        await self.session.execute(statement)
        await self.session.commit()
