from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.base_repository import BaseRepository


class AuditLogRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, audit_log: AuditLog) -> AuditLog:
        self._add_tenant_on_create(audit_log)
        self.session.add(audit_log)
        await self.session.commit()
        await self.session.refresh(audit_log)
        return audit_log

    async def get_by_id(self, audit_log_id: str) -> AuditLog | None:
        statement = select(AuditLog).where(AuditLog.id == audit_log_id)
        statement = self._apply_tenant_filter(statement, AuditLog)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(
        self,
        statement,
        module: str | None = None,
        action: str | None = None,
        entity: str | None = None,
        user_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        q: str | None = None,
    ):
        if module:
            statement = statement.where(AuditLog.module == module)
        if action:
            statement = statement.where(AuditLog.action == action)
        if entity:
            statement = statement.where(AuditLog.entity == entity)
        if user_id:
            statement = statement.where(AuditLog.user_id == user_id)
        if date_from:
            statement = statement.where(AuditLog.created_at >= date_from)
        if date_to:
            statement = statement.where(AuditLog.created_at <= date_to)
        if q:
            like = f"%{q}%"
            statement = statement.where(
                (AuditLog.action.ilike(like)) | (AuditLog.module.ilike(like)) | (AuditLog.entity.ilike(like)) | (AuditLog.entity_id.ilike(like))
            )
        return statement

    async def search(
        self,
        module: str | None = None,
        action: str | None = None,
        entity: str | None = None,
        user_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        statement = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
        statement = self._apply_filters(statement, module, action, entity, user_id, date_from, date_to, q)
        statement = self._apply_tenant_filter(statement, AuditLog)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(
        self,
        module: str | None = None,
        action: str | None = None,
        entity: str | None = None,
        user_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        q: str | None = None,
    ) -> int:
        statement = select(func.count(AuditLog.id))
        statement = self._apply_filters(statement, module, action, entity, user_id, date_from, date_to, q)
        statement = self._apply_tenant_filter(statement, AuditLog)
        result = await self.session.execute(statement)
        return result.scalar_one()
