from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refund import Refund, RefundStatus
from app.models.refund_item import RefundItem
from app.repositories.base_repository import BaseRepository

SORTABLE_FIELDS = {
    "refund_number": Refund.refund_number,
    "amount": Refund.amount,
    "status": Refund.status,
    "created_at": Refund.created_at,
}


class RefundRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, refund: Refund) -> Refund:
        self._add_tenant_on_create(refund)
        self.session.add(refund)
        await self.session.commit()
        await self.session.refresh(refund)
        return refund

    async def save(self, refund: Refund) -> Refund:
        self.session.add(refund)
        await self.session.commit()
        await self.session.refresh(refund)
        return refund

    async def save_no_commit(self, refund: Refund) -> Refund:
        self.session.add(refund)
        await self.session.flush()
        return refund

    async def get_by_id(self, refund_id: str) -> Refund | None:
        statement = select(Refund).where(Refund.id == refund_id)
        statement = self._apply_tenant_filter(statement, Refund)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_number(self, refund_number: str) -> Refund | None:
        statement = select(Refund).where(Refund.refund_number == refund_number)
        statement = self._apply_tenant_filter(statement, Refund)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(
        self,
        statement,
        order_id: str | None = None,
        customer_id: str | None = None,
        status: RefundStatus | None = None,
        q: str | None = None,
    ):
        if order_id is not None:
            statement = statement.where(Refund.order_id == order_id)
        if customer_id is not None:
            statement = statement.where(Refund.customer_id == customer_id)
        if status is not None:
            statement = statement.where(Refund.status == status)
        if q:
            statement = statement.where(or_(Refund.refund_number.ilike(f"%{q}%")))
        return statement

    async def list(
        self,
        order_id: str | None = None,
        customer_id: str | None = None,
        status: RefundStatus | None = None,
        q: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Refund]:
        column = SORTABLE_FIELDS.get(sort_by, Refund.created_at)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(Refund).order_by(order_clause).limit(limit).offset(offset)
        statement = self._apply_filters(statement, order_id, customer_id, status, q)
        statement = self._apply_tenant_filter(statement, Refund)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(
        self,
        order_id: str | None = None,
        customer_id: str | None = None,
        status: RefundStatus | None = None,
        q: str | None = None,
    ) -> int:
        statement = select(func.count(Refund.id))
        statement = self._apply_filters(statement, order_id, customer_id, status, q)
        statement = self._apply_tenant_filter(statement, Refund)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def sum_refunded_for_order(self, order_id: str) -> float:
        # Includes "requested" so a not-yet-approved refund still reserves its
        # amount, preventing two pending requests from together exceeding
        # what's actually refundable on the order.
        statement = select(func.coalesce(func.sum(Refund.amount), 0)).where(
            Refund.order_id == order_id,
            Refund.status.in_([RefundStatus.requested, RefundStatus.approved, RefundStatus.processing, RefundStatus.completed]),
        )
        statement = self._apply_tenant_filter(statement, Refund)
        result = await self.session.execute(statement)
        return result.scalar_one()


class RefundItemRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create_no_commit(self, item: RefundItem) -> RefundItem:
        self._add_tenant_on_create(item)
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_for_refund(self, refund_id: str) -> list[RefundItem]:
        statement = select(RefundItem).where(RefundItem.refund_id == refund_id).order_by(RefundItem.created_at.asc())
        statement = self._apply_tenant_filter(statement, RefundItem)
        result = await self.session.execute(statement)
        return result.scalars().all()
