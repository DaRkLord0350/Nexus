from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import Inventory
from app.repositories.base_repository import BaseRepository

SORTABLE_FIELDS = {
    "quantity_available": Inventory.quantity_available,
    "reorder_point": Inventory.reorder_point,
    "updated_at": Inventory.updated_at,
    "created_at": Inventory.created_at,
}


class InventoryRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def get_by_id(self, inventory_id: str) -> Inventory | None:
        statement = select(Inventory).where(Inventory.id == inventory_id)
        statement = self._apply_tenant_filter(statement, Inventory)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def find_one(self, product_id: str, variant_id: str | None, warehouse_id: str) -> Inventory | None:
        statement = select(Inventory).where(
            Inventory.product_id == product_id,
            Inventory.variant_id == variant_id,
            Inventory.warehouse_id == warehouse_id,
        )
        statement = self._apply_tenant_filter(statement, Inventory)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_or_create_for_update(
        self, product_id: str, variant_id: str | None, warehouse_id: str, bin_id: str | None = None
    ) -> Inventory:
        """Fetches (with a row lock where the backend supports it) or creates the
        Inventory row for this product/variant/warehouse grain. Never commits —
        callers own the transaction boundary so a single commit covers the
        Inventory update and the InventoryTransaction it produces."""
        statement = select(Inventory).where(
            Inventory.product_id == product_id,
            Inventory.variant_id == variant_id,
            Inventory.warehouse_id == warehouse_id,
        )
        statement = self._apply_tenant_filter(statement, Inventory).with_for_update()
        result = await self.session.execute(statement)
        inventory = result.scalar_one_or_none()
        if inventory:
            return inventory

        inventory = Inventory(
            product_id=product_id,
            variant_id=variant_id,
            warehouse_id=warehouse_id,
            bin_id=bin_id,
        )
        self._add_tenant_on_create(inventory)
        self.session.add(inventory)
        await self.session.flush()
        return inventory

    async def save_no_commit(self, inventory: Inventory) -> Inventory:
        self.session.add(inventory)
        await self.session.flush()
        return inventory

    async def save(self, inventory: Inventory) -> Inventory:
        self.session.add(inventory)
        await self.session.commit()
        await self.session.refresh(inventory)
        return inventory

    def _apply_filters(
        self,
        statement,
        warehouse_id: str | None = None,
        product_id: str | None = None,
        low_stock_only: bool = False,
    ):
        if warehouse_id is not None:
            statement = statement.where(Inventory.warehouse_id == warehouse_id)
        if product_id is not None:
            statement = statement.where(Inventory.product_id == product_id)
        if low_stock_only:
            statement = statement.where(
                Inventory.reorder_point.is_not(None),
                Inventory.quantity_available <= Inventory.reorder_point,
            )
        return statement

    async def list(
        self,
        warehouse_id: str | None = None,
        product_id: str | None = None,
        low_stock_only: bool = False,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Inventory]:
        column = SORTABLE_FIELDS.get(sort_by, Inventory.updated_at)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(Inventory).order_by(order_clause).limit(limit).offset(offset)
        statement = self._apply_filters(statement, warehouse_id, product_id, low_stock_only)
        statement = self._apply_tenant_filter(statement, Inventory)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, warehouse_id: str | None = None, product_id: str | None = None, low_stock_only: bool = False) -> int:
        statement = select(func.count(Inventory.id))
        statement = self._apply_filters(statement, warehouse_id, product_id, low_stock_only)
        statement = self._apply_tenant_filter(statement, Inventory)
        result = await self.session.execute(statement)
        return result.scalar_one()
