from typing import Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeMeta


class BaseRepository:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser

    def _apply_tenant_filter(self, statement, model: Type[DeclarativeMeta]):
        # Soft-deleted rows are excluded for everyone, including superusers —
        # deleted_at is a per-row fact, not a tenant-scoping concern, so it's
        # applied unconditionally rather than being subject to the superuser
        # bypass below.
        if hasattr(model, "deleted_at"):
            statement = statement.where(model.deleted_at.is_(None))

        if self.is_superuser or self.organization_id is None:
            return statement
        return statement.where(model.organization_id == self.organization_id)

    def _add_tenant_on_create(self, instance):
        if self.organization_id is not None and getattr(instance, "organization_id", None) is None:
            setattr(instance, "organization_id", self.organization_id)
        return instance
