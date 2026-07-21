from datetime import datetime
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.notification import Notification
from app.repositories.base_repository import BaseRepository


class NotificationRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, notification: Notification) -> Notification:
        self._add_tenant_on_create(notification)
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def list_for_user(self, user_id: str, limit: int = 50, offset: int = 0) -> list[Notification]:
        statement = (
            select(Notification)
            .options(selectinload(Notification.actor))
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        statement = self._apply_tenant_filter(statement, Notification)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count_unread_for_user(self, user_id: str) -> int:
        statement = select(func.count()).select_from(Notification).where(Notification.user_id == user_id, Notification.is_read == False)
        statement = self._apply_tenant_filter(statement, Notification)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def get_by_id(self, notification_id: str) -> Notification | None:
        statement = select(Notification).where(Notification.id == notification_id)
        statement = self._apply_tenant_filter(statement, Notification)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def mark_read(self, notification_id: str) -> None:
        statement = update(Notification).where(Notification.id == notification_id).values(is_read=True, read_at=datetime.utcnow())
        if self.organization_id:
            statement = statement.where(Notification.organization_id == self.organization_id)
        await self.session.execute(statement)
        await self.session.commit()

    async def mark_all_read_for_user(self, user_id: str) -> None:
        statement = update(Notification).where(Notification.user_id == user_id, Notification.is_read == False).values(is_read=True, read_at=datetime.utcnow())
        if self.organization_id:
            statement = statement.where(Notification.organization_id == self.organization_id)
        await self.session.execute(statement)
        await self.session.commit()
