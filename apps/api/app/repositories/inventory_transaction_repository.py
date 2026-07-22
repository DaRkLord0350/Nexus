from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory_transaction import InventoryTransaction, InventoryTransactionType
from app.repositories.base_repository import BaseRepository


class InventoryTransactionRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create_no_commit(self, transaction: InventoryTransaction) -> InventoryTransaction:
        self._add_tenant_on_create(transaction)
        self.session.add(transaction)
        await self.session.flush()
        return transaction

    async def get_by_id(self, transaction_id: str) -> InventoryTransaction | None:
        statement = select(InventoryTransaction).where(InventoryTransaction.id == transaction_id)
        statement = self._apply_tenant_filter(statement, InventoryTransaction)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(
        self,
        statement,
        inventory_id: str | None = None,
        warehouse_id: str | None = None,
        product_id: str | None = None,
        transaction_type: InventoryTransactionType | None = None,
        reference_type: str | None = None,
        reference_id: str | None = None,
    ):
        if inventory_id is not None:
            statement = statement.where(InventoryTransaction.inventory_id == inventory_id)
        if warehouse_id is not None:
            statement = statement.where(InventoryTransaction.warehouse_id == warehouse_id)
        if product_id is not None:
            statement = statement.where(InventoryTransaction.product_id == product_id)
        if transaction_type is not None:
            statement = statement.where(InventoryTransaction.type == transaction_type)
        if reference_type is not None:
            statement = statement.where(InventoryTransaction.reference_type == reference_type)
        if reference_id is not None:
            statement = statement.where(InventoryTransaction.reference_id == reference_id)
        return statement

    async def list(
        self,
        inventory_id: str | None = None,
        warehouse_id: str | None = None,
        product_id: str | None = None,
        transaction_type: InventoryTransactionType | None = None,
        reference_type: str | None = None,
        reference_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[InventoryTransaction]:
        statement = (
            select(InventoryTransaction)
            .order_by(InventoryTransaction.occurred_at.desc())
            .limit(limit)
            .offset(offset)
        )
        statement = self._apply_filters(statement, inventory_id, warehouse_id, product_id, transaction_type, reference_type, reference_id)
        statement = self._apply_tenant_filter(statement, InventoryTransaction)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(
        self,
        inventory_id: str | None = None,
        warehouse_id: str | None = None,
        product_id: str | None = None,
        transaction_type: InventoryTransactionType | None = None,
        reference_type: str | None = None,
        reference_id: str | None = None,
    ) -> int:
        statement = select(func.count(InventoryTransaction.id))
        statement = self._apply_filters(statement, inventory_id, warehouse_id, product_id, transaction_type, reference_type, reference_id)
        statement = self._apply_tenant_filter(statement, InventoryTransaction)
        result = await self.session.execute(statement)
        return result.scalar_one()
