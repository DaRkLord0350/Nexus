from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.return_item import ReturnItem
from app.models.return_request import ReturnRequest, ReturnStatus
from app.repositories.base_repository import BaseRepository

SORTABLE_FIELDS = {
    "return_number": ReturnRequest.return_number,
    "status": ReturnRequest.status,
    "created_at": ReturnRequest.created_at,
}


class ReturnRequestRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, return_request: ReturnRequest) -> ReturnRequest:
        self._add_tenant_on_create(return_request)
        self.session.add(return_request)
        await self.session.commit()
        await self.session.refresh(return_request)
        return return_request

    async def save(self, return_request: ReturnRequest) -> ReturnRequest:
        self.session.add(return_request)
        await self.session.commit()
        await self.session.refresh(return_request)
        return return_request

    async def save_no_commit(self, return_request: ReturnRequest) -> ReturnRequest:
        self.session.add(return_request)
        await self.session.flush()
        return return_request

    async def get_by_id(self, return_id: str) -> ReturnRequest | None:
        statement = select(ReturnRequest).where(ReturnRequest.id == return_id)
        statement = self._apply_tenant_filter(statement, ReturnRequest)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_number(self, return_number: str) -> ReturnRequest | None:
        statement = select(ReturnRequest).where(ReturnRequest.return_number == return_number)
        statement = self._apply_tenant_filter(statement, ReturnRequest)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(
        self,
        statement,
        order_id: str | None = None,
        customer_id: str | None = None,
        status: ReturnStatus | None = None,
        q: str | None = None,
    ):
        if order_id is not None:
            statement = statement.where(ReturnRequest.order_id == order_id)
        if customer_id is not None:
            statement = statement.where(ReturnRequest.customer_id == customer_id)
        if status is not None:
            statement = statement.where(ReturnRequest.status == status)
        if q:
            statement = statement.where(or_(ReturnRequest.return_number.ilike(f"%{q}%")))
        return statement

    async def list(
        self,
        order_id: str | None = None,
        customer_id: str | None = None,
        status: ReturnStatus | None = None,
        q: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReturnRequest]:
        column = SORTABLE_FIELDS.get(sort_by, ReturnRequest.created_at)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(ReturnRequest).order_by(order_clause).limit(limit).offset(offset)
        statement = self._apply_filters(statement, order_id, customer_id, status, q)
        statement = self._apply_tenant_filter(statement, ReturnRequest)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(
        self,
        order_id: str | None = None,
        customer_id: str | None = None,
        status: ReturnStatus | None = None,
        q: str | None = None,
    ) -> int:
        statement = select(func.count(ReturnRequest.id))
        statement = self._apply_filters(statement, order_id, customer_id, status, q)
        statement = self._apply_tenant_filter(statement, ReturnRequest)
        result = await self.session.execute(statement)
        return result.scalar_one()


class ReturnItemRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, item: ReturnItem) -> ReturnItem:
        self._add_tenant_on_create(item)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def create_no_commit(self, item: ReturnItem) -> ReturnItem:
        self._add_tenant_on_create(item)
        self.session.add(item)
        await self.session.flush()
        return item

    async def save(self, item: ReturnItem) -> ReturnItem:
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def save_no_commit(self, item: ReturnItem) -> ReturnItem:
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_by_id(self, item_id: str) -> ReturnItem | None:
        statement = select(ReturnItem).where(ReturnItem.id == item_id)
        statement = self._apply_tenant_filter(statement, ReturnItem)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_return(self, return_request_id: str) -> list[ReturnItem]:
        statement = select(ReturnItem).where(ReturnItem.return_request_id == return_request_id).order_by(ReturnItem.created_at.asc())
        statement = self._apply_tenant_filter(statement, ReturnItem)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def sum_returned_for_order_item(self, order_item_id: str) -> int:
        statement = select(func.coalesce(func.sum(ReturnItem.quantity), 0)).where(ReturnItem.order_item_id == order_item_id)
        statement = self._apply_tenant_filter(statement, ReturnItem)
        result = await self.session.execute(statement)
        return result.scalar_one()
