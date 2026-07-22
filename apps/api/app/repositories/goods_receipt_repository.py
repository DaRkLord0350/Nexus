from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goods_receipt import GoodsReceipt, GoodsReceiptStatus
from app.models.goods_receipt_item import GoodsReceiptItem
from app.repositories.base_repository import BaseRepository


class GoodsReceiptRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, receipt: GoodsReceipt) -> GoodsReceipt:
        self._add_tenant_on_create(receipt)
        self.session.add(receipt)
        await self.session.commit()
        await self.session.refresh(receipt)
        return receipt

    async def save(self, receipt: GoodsReceipt) -> GoodsReceipt:
        self.session.add(receipt)
        await self.session.commit()
        await self.session.refresh(receipt)
        return receipt

    async def save_no_commit(self, receipt: GoodsReceipt) -> GoodsReceipt:
        self.session.add(receipt)
        await self.session.flush()
        return receipt

    async def get_by_id(self, receipt_id: str) -> GoodsReceipt | None:
        statement = select(GoodsReceipt).where(GoodsReceipt.id == receipt_id)
        statement = self._apply_tenant_filter(statement, GoodsReceipt)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_number(self, receipt_number: str) -> GoodsReceipt | None:
        statement = select(GoodsReceipt).where(GoodsReceipt.receipt_number == receipt_number)
        statement = self._apply_tenant_filter(statement, GoodsReceipt)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(
        self,
        statement,
        warehouse_id: str | None = None,
        purchase_order_id: str | None = None,
        status: GoodsReceiptStatus | None = None,
        q: str | None = None,
    ):
        if warehouse_id is not None:
            statement = statement.where(GoodsReceipt.warehouse_id == warehouse_id)
        if purchase_order_id is not None:
            statement = statement.where(GoodsReceipt.purchase_order_id == purchase_order_id)
        if status is not None:
            statement = statement.where(GoodsReceipt.status == status)
        if q:
            like = f"%{q}%"
            statement = statement.where(or_(GoodsReceipt.receipt_number.ilike(like)))
        return statement

    async def list(
        self,
        warehouse_id: str | None = None,
        purchase_order_id: str | None = None,
        status: GoodsReceiptStatus | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[GoodsReceipt]:
        statement = select(GoodsReceipt).order_by(GoodsReceipt.created_at.desc()).limit(limit).offset(offset)
        statement = self._apply_filters(statement, warehouse_id, purchase_order_id, status, q)
        statement = self._apply_tenant_filter(statement, GoodsReceipt)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(
        self,
        warehouse_id: str | None = None,
        purchase_order_id: str | None = None,
        status: GoodsReceiptStatus | None = None,
        q: str | None = None,
    ) -> int:
        statement = select(func.count(GoodsReceipt.id))
        statement = self._apply_filters(statement, warehouse_id, purchase_order_id, status, q)
        statement = self._apply_tenant_filter(statement, GoodsReceipt)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def soft_delete(self, receipt_id: str) -> None:
        statement = update(GoodsReceipt).where(GoodsReceipt.id == receipt_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, GoodsReceipt)
        await self.session.execute(statement)
        await self.session.commit()


class GoodsReceiptItemRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, item: GoodsReceiptItem) -> GoodsReceiptItem:
        self._add_tenant_on_create(item)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def get_by_id(self, item_id: str) -> GoodsReceiptItem | None:
        statement = select(GoodsReceiptItem).where(GoodsReceiptItem.id == item_id)
        statement = self._apply_tenant_filter(statement, GoodsReceiptItem)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_receipt(self, goods_receipt_id: str) -> list[GoodsReceiptItem]:
        statement = select(GoodsReceiptItem).where(GoodsReceiptItem.goods_receipt_id == goods_receipt_id).order_by(GoodsReceiptItem.created_at.asc())
        statement = self._apply_tenant_filter(statement, GoodsReceiptItem)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def delete(self, item_id: str) -> None:
        statement = select(GoodsReceiptItem).where(GoodsReceiptItem.id == item_id)
        statement = self._apply_tenant_filter(statement, GoodsReceiptItem)
        result = await self.session.execute(statement)
        item = result.scalar_one_or_none()
        if item:
            await self.session.delete(item)
            await self.session.commit()
