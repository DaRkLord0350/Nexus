from typing import List

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

    async def get_permission_ids_for_roles(self, role_ids: List[str]) -> dict[str, set[str]]:
        if not role_ids:
            return {}
        statement = select(RolePermission.role_id, RolePermission.permission_id).where(RolePermission.role_id.in_(role_ids))
        result = await self.session.execute(statement)
        permission_ids_by_role: dict[str, set[str]] = {}
        for role_id, permission_id in result.all():
            permission_ids_by_role.setdefault(role_id, set()).add(permission_id)
        return permission_ids_by_role

    async def list_plain(self) -> List[Role]:
        statement = select(Role)
        statement = self._apply_tenant_filter(statement, Role)
        result = await self.session.execute(statement)
        return result.scalars().all()

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

    async def bulk_create(self, roles: List[Role]) -> List[Role]:
        for role in roles:
            self._add_tenant_on_create(role)
        self.session.add_all(roles)
        await self.session.commit()
        return roles

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

    async def bulk_add_permissions(self, role_permissions: List[RolePermission]) -> None:
        for role_permission in role_permissions:
            self._add_tenant_on_create(role_permission)
        self.session.add_all(role_permissions)
        await self.session.commit()

    async def remove_permission(self, role_id: str, permission_id: str) -> None:
        statement = delete(RolePermission).where(RolePermission.role_id == role_id, RolePermission.permission_id == permission_id)
        await self.session.execute(statement)
        await self.session.commit()
