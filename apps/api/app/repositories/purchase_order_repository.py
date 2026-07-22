from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.purchase_order import PurchaseOrder, PurchaseOrderStatus
from app.models.purchase_order_item import PurchaseOrderItem
from app.repositories.base_repository import BaseRepository

SORTABLE_FIELDS = {
    "po_number": PurchaseOrder.po_number,
    "expected_date": PurchaseOrder.expected_date,
    "total": PurchaseOrder.total,
    "created_at": PurchaseOrder.created_at,
}


class PurchaseOrderRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, purchase_order: PurchaseOrder) -> PurchaseOrder:
        self._add_tenant_on_create(purchase_order)
        self.session.add(purchase_order)
        await self.session.commit()
        await self.session.refresh(purchase_order)
        return purchase_order

    async def save(self, purchase_order: PurchaseOrder) -> PurchaseOrder:
        self.session.add(purchase_order)
        await self.session.commit()
        await self.session.refresh(purchase_order)
        return purchase_order

    async def save_no_commit(self, purchase_order: PurchaseOrder) -> PurchaseOrder:
        self.session.add(purchase_order)
        await self.session.flush()
        return purchase_order

    async def get_by_id(self, po_id: str) -> PurchaseOrder | None:
        statement = select(PurchaseOrder).where(PurchaseOrder.id == po_id)
        statement = self._apply_tenant_filter(statement, PurchaseOrder)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_number(self, po_number: str) -> PurchaseOrder | None:
        statement = select(PurchaseOrder).where(PurchaseOrder.po_number == po_number)
        statement = self._apply_tenant_filter(statement, PurchaseOrder)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(
        self,
        statement,
        warehouse_id: str | None = None,
        status: PurchaseOrderStatus | None = None,
        q: str | None = None,
    ):
        if warehouse_id is not None:
            statement = statement.where(PurchaseOrder.warehouse_id == warehouse_id)
        if status is not None:
            statement = statement.where(PurchaseOrder.status == status)
        if q:
            like = f"%{q}%"
            statement = statement.where(or_(PurchaseOrder.po_number.ilike(like), PurchaseOrder.supplier_name.ilike(like)))
        return statement

    async def list(
        self,
        warehouse_id: str | None = None,
        status: PurchaseOrderStatus | None = None,
        q: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[PurchaseOrder]:
        column = SORTABLE_FIELDS.get(sort_by, PurchaseOrder.created_at)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(PurchaseOrder).order_by(order_clause).limit(limit).offset(offset)
        statement = self._apply_filters(statement, warehouse_id, status, q)
        statement = self._apply_tenant_filter(statement, PurchaseOrder)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, warehouse_id: str | None = None, status: PurchaseOrderStatus | None = None, q: str | None = None) -> int:
        statement = select(func.count(PurchaseOrder.id))
        statement = self._apply_filters(statement, warehouse_id, status, q)
        statement = self._apply_tenant_filter(statement, PurchaseOrder)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def soft_delete(self, po_id: str) -> None:
        statement = update(PurchaseOrder).where(PurchaseOrder.id == po_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, PurchaseOrder)
        await self.session.execute(statement)
        await self.session.commit()


class PurchaseOrderItemRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, item: PurchaseOrderItem) -> PurchaseOrderItem:
        self._add_tenant_on_create(item)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def save(self, item: PurchaseOrderItem) -> PurchaseOrderItem:
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def save_no_commit(self, item: PurchaseOrderItem) -> PurchaseOrderItem:
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_by_id(self, item_id: str) -> PurchaseOrderItem | None:
        statement = select(PurchaseOrderItem).where(PurchaseOrderItem.id == item_id)
        statement = self._apply_tenant_filter(statement, PurchaseOrderItem)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_order(self, purchase_order_id: str) -> list[PurchaseOrderItem]:
        statement = select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == purchase_order_id).order_by(PurchaseOrderItem.created_at.asc())
        statement = self._apply_tenant_filter(statement, PurchaseOrderItem)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def delete(self, item_id: str) -> None:
        statement = select(PurchaseOrderItem).where(PurchaseOrderItem.id == item_id)
        statement = self._apply_tenant_filter(statement, PurchaseOrderItem)
        result = await self.session.execute(statement)
        item = result.scalar_one_or_none()
        if item:
            await self.session.delete(item)
            await self.session.commit()
