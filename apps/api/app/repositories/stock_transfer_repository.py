from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock_transfer import StockTransfer, StockTransferStatus
from app.models.stock_transfer_item import StockTransferItem
from app.repositories.base_repository import BaseRepository


class StockTransferRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, transfer: StockTransfer) -> StockTransfer:
        self._add_tenant_on_create(transfer)
        self.session.add(transfer)
        await self.session.commit()
        await self.session.refresh(transfer)
        return transfer

    async def save(self, transfer: StockTransfer) -> StockTransfer:
        self.session.add(transfer)
        await self.session.commit()
        await self.session.refresh(transfer)
        return transfer

    async def get_by_id(self, transfer_id: str) -> StockTransfer | None:
        statement = select(StockTransfer).where(StockTransfer.id == transfer_id)
        statement = self._apply_tenant_filter(statement, StockTransfer)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_number(self, transfer_number: str) -> StockTransfer | None:
        statement = select(StockTransfer).where(StockTransfer.transfer_number == transfer_number)
        statement = self._apply_tenant_filter(statement, StockTransfer)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(
        self,
        statement,
        from_warehouse_id: str | None = None,
        to_warehouse_id: str | None = None,
        status: StockTransferStatus | None = None,
        q: str | None = None,
    ):
        if from_warehouse_id is not None:
            statement = statement.where(StockTransfer.from_warehouse_id == from_warehouse_id)
        if to_warehouse_id is not None:
            statement = statement.where(StockTransfer.to_warehouse_id == to_warehouse_id)
        if status is not None:
            statement = statement.where(StockTransfer.status == status)
        if q:
            like = f"%{q}%"
            statement = statement.where(or_(StockTransfer.transfer_number.ilike(like)))
        return statement

    async def list(
        self,
        from_warehouse_id: str | None = None,
        to_warehouse_id: str | None = None,
        status: StockTransferStatus | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StockTransfer]:
        statement = select(StockTransfer).order_by(StockTransfer.created_at.desc()).limit(limit).offset(offset)
        statement = self._apply_filters(statement, from_warehouse_id, to_warehouse_id, status, q)
        statement = self._apply_tenant_filter(statement, StockTransfer)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(
        self,
        from_warehouse_id: str | None = None,
        to_warehouse_id: str | None = None,
        status: StockTransferStatus | None = None,
        q: str | None = None,
    ) -> int:
        statement = select(func.count(StockTransfer.id))
        statement = self._apply_filters(statement, from_warehouse_id, to_warehouse_id, status, q)
        statement = self._apply_tenant_filter(statement, StockTransfer)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def soft_delete(self, transfer_id: str) -> None:
        statement = update(StockTransfer).where(StockTransfer.id == transfer_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, StockTransfer)
        await self.session.execute(statement)
        await self.session.commit()


class StockTransferItemRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, item: StockTransferItem) -> StockTransferItem:
        self._add_tenant_on_create(item)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def save(self, item: StockTransferItem) -> StockTransferItem:
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def get_by_id(self, item_id: str) -> StockTransferItem | None:
        statement = select(StockTransferItem).where(StockTransferItem.id == item_id)
        statement = self._apply_tenant_filter(statement, StockTransferItem)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_transfer(self, stock_transfer_id: str) -> list[StockTransferItem]:
        statement = select(StockTransferItem).where(StockTransferItem.stock_transfer_id == stock_transfer_id).order_by(StockTransferItem.created_at.asc())
        statement = self._apply_tenant_filter(statement, StockTransferItem)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def delete(self, item_id: str) -> None:
        statement = select(StockTransferItem).where(StockTransferItem.id == item_id)
        statement = self._apply_tenant_filter(statement, StockTransferItem)
        result = await self.session.execute(statement)
        item = result.scalar_one_or_none()
        if item:
            await self.session.delete(item)
            await self.session.commit()
