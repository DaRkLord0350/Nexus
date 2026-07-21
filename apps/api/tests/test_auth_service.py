import asyncio
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db import Base
from app.services.auth_service import AuthService


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


def test_register_login_and_refresh(app_session: AsyncSession):
    async def _run_test():
        auth_service = AuthService(app_session)

        user = await auth_service.register_user(
            email="alice@example.com",
            first_name="Alice",
            last_name="Walker",
            password="StrongPassw0rd!",
            organization_name="CommerceOS Test",
        )

        assert user.email == "alice@example.com"
        assert user.organization_id is not None
        assert not user.is_verified

        token_data = await auth_service.login(
            email="alice@example.com",
            password="StrongPassw0rd!",
            device_name="pytest",
            device_type="test",
            ip_address="127.0.0.1",
            user_agent="pytest-agent",
        )

        assert token_data["access_token"]
        assert token_data["refresh_token"]
        assert token_data["token_type"] == "bearer"

        refresh_data = await auth_service.refresh(token_data["refresh_token"])
        assert refresh_data["access_token"]
        assert refresh_data["refresh_token"] != token_data["refresh_token"]

    asyncio.run(_run_test())


def test_reset_password_revokes_all_existing_sessions(app_session: AsyncSession):
    async def _run_test():
        from datetime import datetime, timedelta

        from app.models.password_reset_token import PasswordResetToken
        from app.repositories.session_repository import SessionRepository
        from app.utils.tokens import generate_token, hash_token

        auth_service = AuthService(app_session)
        user = await auth_service.register_user(
            email="revoke@example.com",
            first_name="Revoke",
            last_name="Tester",
            password="StrongPassw0rd!",
            organization_name="Revoke Test Org",
        )
        await auth_service.login(
            email="revoke@example.com",
            password="StrongPassw0rd!",
            device_name="pytest",
            device_type="test",
            ip_address="127.0.0.1",
            user_agent="pytest-agent",
        )

        session_repo = SessionRepository(app_session, organization_id=user.organization_id)
        sessions_before = await session_repo.list_recent()
        assert len(sessions_before) == 1
        assert sessions_before[0].revoked is False

        reset_token = generate_token(64)
        app_session.add(PasswordResetToken(
            user_id=user.id,
            organization_id=user.organization_id,
            token_hash=hash_token(reset_token),
            expires_at=datetime.utcnow() + timedelta(hours=2),
            revoked=False,
        ))
        await app_session.commit()

        await auth_service.reset_password(reset_token, "BrandNewPassword123!")

        # list_recent() only returns non-revoked sessions — a real fix means
        # this comes back empty; before the fix, revoke_all_for_user() built
        # an UPDATE statement with no .values(), so it silently did nothing.
        sessions_after = await session_repo.list_recent()
        assert sessions_after == []

    asyncio.run(_run_test())

