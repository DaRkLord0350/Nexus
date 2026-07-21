import csv
import io
import logging
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository

logger = logging.getLogger("app.audit")

CSV_COLUMNS = [
    "id",
    "created_at",
    "user_id",
    "action",
    "module",
    "entity",
    "entity_id",
    "ip_address",
    "user_agent",
    "request_id",
]


class AuditService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = AuditLogRepository(session, organization_id, is_superuser)

    async def log(
        self,
        *,
        action: str,
        module: str,
        entity: str | None = None,
        entity_id: str | None = None,
        user_id: str | None = None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        context: AuditContext | None = None,
        organization_id: str | None = None,
    ) -> AuditLog | None:
        """Best-effort audit logging. Never raises — a failed audit write must not break the primary action."""
        try:
            record = AuditLog(
                action=action,
                module=module,
                entity=entity,
                entity_id=entity_id,
                user_id=user_id,
                before=before,
                after=after,
                ip_address=context.ip_address if context else None,
                user_agent=context.user_agent if context else None,
                request_id=context.request_id if context else None,
            )
            target_org_id = organization_id or self.organization_id
            if target_org_id:
                record.organization_id = target_org_id
            created = await self.repo.create(record)
            logger.info(
                "audit_log_created",
                extra={"structured": {"audit_id": created.id, "action": action, "module": module, "entity": entity, "entity_id": entity_id}},
            )
            return created
        except Exception:
            logger.exception("Failed to write audit log for action=%s module=%s", action, module)
            await self.session.rollback()
            return None

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
    ) -> tuple[list[AuditLog], int]:
        items = await self.repo.search(module, action, entity, user_id, date_from, date_to, q, limit=limit, offset=offset)
        total = await self.repo.count(module, action, entity, user_id, date_from, date_to, q)
        return items, total

    async def export_csv(
        self,
        module: str | None = None,
        action: str | None = None,
        entity: str | None = None,
        user_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        q: str | None = None,
        max_rows: int = 10000,
    ) -> str:
        items = await self.repo.search(module, action, entity, user_id, date_from, date_to, q, limit=max_rows, offset=0)
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for item in items:
            writer.writerow({
                "id": item.id,
                "created_at": item.created_at.isoformat(),
                "user_id": item.user_id or "",
                "action": item.action,
                "module": item.module,
                "entity": item.entity or "",
                "entity_id": item.entity_id or "",
                "ip_address": item.ip_address or "",
                "user_agent": item.user_agent or "",
                "request_id": item.request_id or "",
            })
        return buffer.getvalue()
