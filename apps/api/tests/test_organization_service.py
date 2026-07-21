import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.services.auth_service import AuthService
from app.services.organization_service import OrganizationService


@pytest.fixture
def app_session(tmp_path) -> AsyncSession:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    engine = create_async_engine(database_url, future=True)

    async def initialize_database() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(initialize_database())
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    session = async_session()

    try:
        yield session
    finally:
        asyncio.run(session.close())
        asyncio.run(engine.dispose())


def test_deactivating_organization_revokes_all_member_sessions(app_session: AsyncSession):
    async def _run_test():
        from app.repositories.session_repository import SessionRepository

        auth_service = AuthService(app_session)
        user = await auth_service.register_user(
            email="member@example.com",
            first_name="Member",
            last_name="Tester",
            password="SecurePass456!",
            organization_name="Suspend Test Org",
        )
        await auth_service.login(
            email="member@example.com",
            password="SecurePass456!",
            device_name="pytest",
            device_type="test",
            ip_address="127.0.0.1",
            user_agent="pytest-agent",
        )

        session_repo = SessionRepository(app_session, organization_id=user.organization_id)
        assert len(await session_repo.list_recent()) == 1

        organization_service = OrganizationService(app_session)
        await organization_service.deactivate_organization(user.organization_id)

        assert await session_repo.list_recent() == []

    asyncio.run(_run_test())


def test_deleted_organization_is_no_longer_retrievable(app_session: AsyncSession):
    async def _run_test():
        auth_service = AuthService(app_session)
        user = await auth_service.register_user(
            email="owner@example.com",
            first_name="Owner",
            last_name="Tester",
            password="SecurePass456!",
            organization_name="Soft Delete Org",
        )

        organization_service = OrganizationService(app_session)
        found_before = await organization_service.get_organization(user.organization_id)
        assert found_before is not None

        deleted = await organization_service.delete_organization(user.organization_id)
        assert deleted.deleted_at is not None

        found_after = await organization_service.get_organization(user.organization_id)
        assert found_after is None

    asyncio.run(_run_test())

