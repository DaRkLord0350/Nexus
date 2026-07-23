from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment_attempt import PaymentAttempt
from app.repositories.base_repository import BaseRepository


class PaymentAttemptRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, attempt: PaymentAttempt) -> PaymentAttempt:
        self._add_tenant_on_create(attempt)
        self.session.add(attempt)
        await self.session.commit()
        await self.session.refresh(attempt)
        return attempt

    async def get_by_id(self, attempt_id: str) -> PaymentAttempt | None:
        statement = select(PaymentAttempt).where(PaymentAttempt.id == attempt_id)
        statement = self._apply_tenant_filter(statement, PaymentAttempt)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, idempotency_key: str) -> PaymentAttempt | None:
        statement = select(PaymentAttempt).where(PaymentAttempt.idempotency_key == idempotency_key)
        statement = self._apply_tenant_filter(statement, PaymentAttempt)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_order(self, order_id: str) -> list[PaymentAttempt]:
        statement = select(PaymentAttempt).where(PaymentAttempt.order_id == order_id).order_by(PaymentAttempt.created_at.desc())
        statement = self._apply_tenant_filter(statement, PaymentAttempt)
        result = await self.session.execute(statement)
        return result.scalars().all()
