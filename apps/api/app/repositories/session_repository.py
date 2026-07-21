from datetime import datetime, timedelta
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.session import Session
from app.repositories.base_repository import BaseRepository


class SessionRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, session_record: Session) -> Session:
        self._add_tenant_on_create(session_record)
        self.session.add(session_record)
        await self.session.commit()
        await self.session.refresh(session_record)
        return session_record

    async def get_by_id(self, session_id: str) -> Session | None:
        statement = select(Session).where(Session.id == session_id)
        statement = self._apply_tenant_filter(statement, Session)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def count_recent(self, days: int = 7) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        statement = select(func.count()).select_from(Session).where(Session.last_active_at >= cutoff, Session.revoked == False)
        statement = self._apply_tenant_filter(statement, Session)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def list_recent(self, limit: int = 10) -> list[Session]:
        statement = (
            select(Session)
            .options(selectinload(Session.user))
            .where(Session.revoked == False)
            .order_by(Session.last_active_at.desc())
            .limit(limit)
        )
        statement = self._apply_tenant_filter(statement, Session)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def revoke(self, session_id: str) -> None:
        statement = update(Session).where(Session.id == session_id)
        if self.organization_id:
            statement = statement.where(Session.organization_id == self.organization_id)
        statement = statement.values(revoked=True)
        await self.session.execute(statement)
        await self.session.commit()

    async def revoke_all_for_user(self, user_id: str) -> None:
        statement = update(Session).where(Session.user_id == user_id).values(revoked=True)
        if self.organization_id:
            statement = statement.where(Session.organization_id == self.organization_id)
        await self.session.execute(statement)
        await self.session.commit()

    async def revoke_all_for_organization(self, organization_id: str) -> None:
        statement = update(Session).where(Session.organization_id == organization_id).values(revoked=True)
        await self.session.execute(statement)
        await self.session.commit()
