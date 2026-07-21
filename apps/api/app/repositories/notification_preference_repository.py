from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification_preference import NotificationPreference, NotificationChannel
from app.repositories.base_repository import BaseRepository


class NotificationPreferenceRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def get_for_user(self, user_id: str) -> list[NotificationPreference]:
        statement = select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        statement = self._apply_tenant_filter(statement, NotificationPreference)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_for_user_by_channel(self, user_id: str, channel: NotificationChannel) -> NotificationPreference | None:
        statement = select(NotificationPreference).where(NotificationPreference.user_id == user_id, NotificationPreference.channel == channel)
        statement = self._apply_tenant_filter(statement, NotificationPreference)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def set_preference(self, preference: NotificationPreference) -> NotificationPreference:
        self._add_tenant_on_create(preference)
        self.session.add(preference)
        await self.session.commit()
        await self.session.refresh(preference)
        return preference

    async def upsert(self, user_id: str, channel: NotificationChannel, enabled: bool) -> NotificationPreference:
        existing = await self.get_for_user_by_channel(user_id, channel)
        if existing:
            existing.enabled = enabled
            self.session.add(existing)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        preference = NotificationPreference(user_id=user_id, channel=channel, enabled=enabled)
        self._add_tenant_on_create(preference)
        self.session.add(preference)
        await self.session.commit()
        await self.session.refresh(preference)
        return preference
