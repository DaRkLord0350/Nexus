from __future__ import annotations

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderPriority, OrderStatus
from app.models.order_item import OrderItem
from app.models.order_note import OrderNote
from app.models.order_status_history import OrderStatusHistory
from app.repositories.base_repository import BaseRepository

SORTABLE_FIELDS = {
    "order_number": Order.order_number,
    "total": Order.total,
    "status": Order.status,
    "created_at": Order.created_at,
    "updated_at": Order.updated_at,
}


class OrderRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, order: Order) -> Order:
        self._add_tenant_on_create(order)
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def save(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def save_no_commit(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.flush()
        return order

    async def get_by_id(self, order_id: str) -> Order | None:
        statement = select(Order).where(Order.id == order_id)
        statement = self._apply_tenant_filter(statement, Order)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_number(self, order_number: str) -> Order | None:
        statement = select(Order).where(Order.order_number == order_number)
        statement = self._apply_tenant_filter(statement, Order)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(
        self,
        statement,
        customer_id: str | None = None,
        status: OrderStatus | None = None,
        priority: OrderPriority | None = None,
        requires_manual_review: bool | None = None,
        q: str | None = None,
    ):
        if customer_id is not None:
            statement = statement.where(Order.customer_id == customer_id)
        if status is not None:
            statement = statement.where(Order.status == status)
        if priority is not None:
            statement = statement.where(Order.priority == priority)
        if requires_manual_review is not None:
            statement = statement.where(Order.requires_manual_review == requires_manual_review)
        if q:
            like = f"%{q}%"
            statement = statement.where(
                or_(Order.order_number.ilike(like), Order.billing_first_name.ilike(like), Order.billing_last_name.ilike(like), Order.tags.ilike(like))
            )
        return statement

    async def list(
        self,
        customer_id: str | None = None,
        status: OrderStatus | None = None,
        priority: OrderPriority | None = None,
        requires_manual_review: bool | None = None,
        q: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Order]:
        column = SORTABLE_FIELDS.get(sort_by, Order.created_at)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(Order).order_by(order_clause).limit(limit).offset(offset)
        statement = self._apply_filters(statement, customer_id, status, priority, requires_manual_review, q)
        statement = self._apply_tenant_filter(statement, Order)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(
        self,
        customer_id: str | None = None,
        status: OrderStatus | None = None,
        priority: OrderPriority | None = None,
        requires_manual_review: bool | None = None,
        q: str | None = None,
    ) -> int:
        statement = select(func.count(Order.id))
        statement = self._apply_filters(statement, customer_id, status, priority, requires_manual_review, q)
        statement = self._apply_tenant_filter(statement, Order)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def bulk_update_priority(self, order_ids: list[str], priority: OrderPriority) -> int:
        if not order_ids:
            return 0
        statement = update(Order).where(Order.id.in_(order_ids)).values(priority=priority)
        statement = self._apply_tenant_filter(statement, Order)
        result = await self.session.execute(statement)
        await self.session.commit()
        return result.rowcount or 0

    async def bulk_update_tags(self, order_ids: list[str], tags: str) -> int:
        if not order_ids:
            return 0
        statement = update(Order).where(Order.id.in_(order_ids)).values(tags=tags)
        statement = self._apply_tenant_filter(statement, Order)
        result = await self.session.execute(statement)
        await self.session.commit()
        return result.rowcount or 0


class OrderItemRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, item: OrderItem) -> OrderItem:
        self._add_tenant_on_create(item)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def create_no_commit(self, item: OrderItem) -> OrderItem:
        self._add_tenant_on_create(item)
        self.session.add(item)
        await self.session.flush()
        return item

    async def save(self, item: OrderItem) -> OrderItem:
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def save_no_commit(self, item: OrderItem) -> OrderItem:
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_by_id(self, item_id: str) -> OrderItem | None:
        statement = select(OrderItem).where(OrderItem.id == item_id)
        statement = self._apply_tenant_filter(statement, OrderItem)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_order(self, order_id: str) -> list[OrderItem]:
        statement = select(OrderItem).where(OrderItem.order_id == order_id).order_by(OrderItem.created_at.asc())
        statement = self._apply_tenant_filter(statement, OrderItem)
        result = await self.session.execute(statement)
        return result.scalars().all()


class OrderStatusHistoryRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create_no_commit(self, entry: OrderStatusHistory) -> OrderStatusHistory:
        self._add_tenant_on_create(entry)
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def list_for_order(self, order_id: str) -> list[OrderStatusHistory]:
        statement = select(OrderStatusHistory).where(OrderStatusHistory.order_id == order_id).order_by(OrderStatusHistory.changed_at.asc())
        statement = self._apply_tenant_filter(statement, OrderStatusHistory)
        result = await self.session.execute(statement)
        return result.scalars().all()


class OrderNoteRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, note: OrderNote) -> OrderNote:
        self._add_tenant_on_create(note)
        self.session.add(note)
        await self.session.commit()
        await self.session.refresh(note)
        return note

    async def list_for_order(self, order_id: str) -> list[OrderNote]:
        statement = select(OrderNote).where(OrderNote.order_id == order_id).order_by(OrderNote.created_at.desc())
        statement = self._apply_tenant_filter(statement, OrderNote)
        result = await self.session.execute(statement)
        return result.scalars().all()
