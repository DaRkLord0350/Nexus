import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db import Base
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
