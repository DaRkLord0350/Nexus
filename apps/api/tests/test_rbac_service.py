import asyncio

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db import Base
from app.models.role_permission import RolePermission
from app.services.auth_service import AuthService
from app.services.permission_service import PermissionService
from app.services.rbac_service import RBACService


async def _create_session(database_url: str) -> AsyncSession:
    engine = create_async_engine(database_url, future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    return async_session()


def test_rbac_default_roles_and_permissions():
    async def run_test():
        database_url = "sqlite+aiosqlite:///:memory:"
        session = await _create_session(database_url)
        try:
            auth_service = AuthService(session)
            user = await auth_service.register_user(
                email="owner@example.com",
                first_name="Owner",
                last_name="User",
                password="StrongPass123!",
                organization_name="CommerceOS RBAC",
            )

            rbac_service = RBACService(session, organization_id=user.organization_id)
            roles = await rbac_service.list_roles()
            assert any(role.name == "Owner" for role in roles)

            permissions = await rbac_service.list_permissions()
            permission_codes = {permission.code for permission in permissions}
            assert "users" in permission_codes
            assert "orders" in permission_codes

            permission_service = PermissionService(session, organization_id=user.organization_id)
            assert await permission_service.has_permission(user.id, "users")
            assert await permission_service.has_permission(user.id, "analytics")
        finally:
            await session.close()

    asyncio.run(run_test())


def test_has_permission_with_overlapping_roles_does_not_raise():
    """Regression test: a user holding two roles that both grant the same
    permission (e.g. Owner + Admin, which have identical default permission
    sets) must not make has_permission() raise MultipleResultsFound. The
    join through user_roles can legitimately match more than one row —
    has_permission() must treat this as an existence check, not assume
    uniqueness."""

    async def run_test():
        database_url = "sqlite+aiosqlite:///:memory:"
        session = await _create_session(database_url)
        try:
            auth_service = AuthService(session)
            user = await auth_service.register_user(
                email="dual-role@example.com",
                first_name="Dual",
                last_name="Role",
                password="StrongPass123!",
                organization_name="CommerceOS Dual Role",
            )

            rbac_service = RBACService(session, organization_id=user.organization_id)
            roles = {role.name: role for role in await rbac_service.list_roles()}

            # register_user() already assigns "Owner". Assigning "Admin" too
            # reproduces the real-world scenario: both roles grant the exact
            # same default permission set, so any permission check for this
            # user now matches via two separate roles.
            await rbac_service.assign_role_to_user(user.id, roles["Admin"].id)

            permission_service = PermissionService(session, organization_id=user.organization_id)

            # Must not raise sqlalchemy.exc.MultipleResultsFound.
            assert await permission_service.has_permission(user.id, "users") is True
            assert await permission_service.has_permission(user.id, "catalog.products.view") is True
            assert await permission_service.has_permission(user.id, "not-a-real-permission") is False
        finally:
            await session.close()

    asyncio.run(run_test())


def test_role_permissions_unique_constraint_prevents_duplicates():
    """Regression test: the database itself must never accumulate duplicate
    (role_id, permission_id) mappings, regardless of what application code
    attempts. This is the invariant the RBAC batching optimization relies on
    to stay correct."""

    async def run_test():
        database_url = "sqlite+aiosqlite:///:memory:"
        session = await _create_session(database_url)
        try:
            auth_service = AuthService(session)
            user = await auth_service.register_user(
                email="dupe-check@example.com",
                first_name="Dupe",
                last_name="Check",
                password="StrongPass123!",
                organization_name="CommerceOS Dupe Check",
            )

            rbac_service = RBACService(session, organization_id=user.organization_id)
            roles = {role.name: role for role in await rbac_service.list_roles()}
            permissions = {permission.code: permission for permission in await rbac_service.list_permissions()}

            owner_role = roles["Owner"]
            some_permission = permissions["users"]

            with pytest.raises(IntegrityError):
                session.add(
                    RolePermission(
                        role_id=owner_role.id,
                        permission_id=some_permission.id,
                        organization_id=owner_role.organization_id,
                    )
                )
                await session.commit()
        finally:
            await session.rollback()
            await session.close()

    asyncio.run(run_test())
