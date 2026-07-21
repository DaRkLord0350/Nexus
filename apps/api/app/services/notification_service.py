from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationChannel as ModelNotificationChannel, NotificationType
from app.models.notification_preference import NotificationPreference, NotificationChannel as PreferenceNotificationChannel
from app.repositories.notification_preference_repository import NotificationPreferenceRepository
from app.repositories.notification_repository import NotificationRepository
from app.services.email_service import EmailService
from app.notifications.publisher import NotificationPublisher


class NotificationService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.notification_repo = NotificationRepository(session, organization_id, is_superuser)
        self.preference_repo = NotificationPreferenceRepository(session, organization_id, is_superuser)
        self.email_service = EmailService()

    async def send_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.info,
        channels: list[ModelNotificationChannel] | None = None,
        actor_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Notification:
        if channels is None:
            channels = [ModelNotificationChannel.in_app, ModelNotificationChannel.email]

        enabled_channels = []
        for channel in channels:
            if channel == ModelNotificationChannel.email:
                preference = await self.preference_repo.get_for_user_by_channel(user_id, PreferenceNotificationChannel.email)
                if preference is not None and not preference.enabled:
                    continue
            enabled_channels.append(channel)

        stored_channel = ModelNotificationChannel.in_app if ModelNotificationChannel.in_app in enabled_channels else (enabled_channels[0] if enabled_channels else ModelNotificationChannel.database)
        notification = Notification(
            user_id=user_id,
            actor_id=actor_id,
            title=title,
            message=message,
            type=notification_type,
            channel=stored_channel,
            # Note: the column is named `payload`, not `metadata` — every
            # SQLAlchemy declarative model already has a class-level
            # `metadata` attribute (the table's MetaData), so passing
            # metadata=... here would silently overwrite that instance
            # attribute instead of persisting anything.
            payload=metadata,
            is_read=False,
        )
        notification = await self.notification_repo.create(notification)

        await NotificationPublisher.publish(self.organization_id or "", user_id, {
            "id": notification.id,
            "title": title,
            "message": message,
            "type": notification_type.value,
            "channel": notification.channel.value,
            "created_at": notification.created_at.isoformat(),
            "is_read": notification.is_read,
        })

        if ModelNotificationChannel.email in enabled_channels and self.email_service:
            await self.email_service.send_email(
                recipient=await self._get_user_email(user_id),
                subject=title,
                body=message,
            )

        return notification

    async def _get_user_email(self, user_id: str) -> str:
        from app.repositories.user_repository import UserRepository

        user = await UserRepository(self.session, organization_id=self.organization_id).get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return user.email

    async def list_notifications(self, user_id: str, limit: int = 50, offset: int = 0) -> list[Notification]:
        return await self.notification_repo.list_for_user(user_id, limit=limit, offset=offset)

    async def get_unread_count(self, user_id: str) -> int:
        return await self.notification_repo.count_unread_for_user(user_id)

    async def mark_read(self, notification_id: str, user_id: str) -> None:
        notification = await self.notification_repo.get_by_id(notification_id)
        if not notification or notification.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
        await self.notification_repo.mark_read(notification_id)

    async def mark_all_read(self, user_id: str) -> None:
        await self.notification_repo.mark_all_read_for_user(user_id)

    async def get_preferences(self, user_id: str) -> list[NotificationPreference]:
        return await self.preference_repo.get_for_user(user_id)

    async def update_preference(self, user_id: str, channel: PreferenceNotificationChannel, enabled: bool) -> NotificationPreference:
        return await self.preference_repo.upsert(user_id, channel, enabled)
