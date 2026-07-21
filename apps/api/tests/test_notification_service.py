import asyncio
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db import Base
from app.models.notification import NotificationChannel as ModelNotificationChannel, NotificationType
from app.models.notification_preference import NotificationChannel as PreferenceNotificationChannel
from app.services.auth_service import AuthService
from app.services.notification_service import NotificationService
import app.notifications.publisher as publisher


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


def test_notification_lifecycle(app_session: AsyncSession, monkeypatch):
    async def _run_test():
        auth_service = AuthService(app_session)
        user = await auth_service.register_user(
            email="alice@example.com",
            first_name="Alice",
            last_name="Walker",
            password="SecurePass123!",
            organization_name="CommerceOS Test",
        )

        async def noop_publish(*_args, **_kwargs):
            return None

        monkeypatch.setattr(publisher.NotificationPublisher, "publish", staticmethod(noop_publish))

        notification_service = NotificationService(app_session, organization_id=user.organization_id)
        notification = await notification_service.send_notification(
            user_id=user.id,
            title="Welcome to CommerceOS",
            message="Your account is active and notifications are enabled.",
            notification_type=NotificationType.info,
            channels=[ModelNotificationChannel.in_app],
            actor_id=user.id,
            metadata={"source": "unit-test"},
        )

        assert notification.id
        assert notification.user_id == user.id
        assert notification.type == NotificationType.info
        assert notification.payload == {"source": "unit-test"}

        notifications = await notification_service.list_notifications(user.id)
        assert len(notifications) == 1
        # Re-fetched from the DB (not the in-memory object above) — this is
        # the check that actually proves the payload was persisted, not just
        # held in memory on the object `send_notification` returned.
        assert notifications[0].payload == {"source": "unit-test"}

        unread_count = await notification_service.get_unread_count(user.id)
        assert unread_count == 1

        await notification_service.mark_read(notification.id, user.id)
        assert await notification_service.get_unread_count(user.id) == 0

        await notification_service.mark_all_read(user.id)
        assert await notification_service.get_unread_count(user.id) == 0

        preference = await notification_service.update_preference(user.id, PreferenceNotificationChannel.email, False)
        assert preference.channel == PreferenceNotificationChannel.email
        assert preference.enabled is False

    asyncio.run(_run_test())
