from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import Inventory
from app.models.inventory_transaction import InventoryTransaction, InventoryTransactionType
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.inventory_transaction_repository import InventoryTransactionRepository


class InventoryService:
    """Read/query side of inventory plus configuration edits (bin, min/max,
    reorder point). All quantity mutations go through StockMovementService —
    this service never writes to the quantity_* columns."""

    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = InventoryRepository(session, organization_id, is_superuser)
        self.transaction_repo = InventoryTransactionRepository(session, organization_id, is_superuser)

    async def get_inventory(self, inventory_id: str) -> Inventory | None:
        return await self.repo.get_by_id(inventory_id)

    async def list_inventory(
        self,
        warehouse_id: str | None = None,
        product_id: str | None = None,
        low_stock_only: bool = False,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Inventory], int]:
        items = await self.repo.list(warehouse_id, product_id, low_stock_only, sort_by, sort_order, limit, offset)
        total = await self.repo.count(warehouse_id, product_id, low_stock_only)
        return items, total

    async def update_inventory(self, inventory_id: str, data) -> Inventory:
        inventory = await self.repo.get_by_id(inventory_id)
        if not inventory:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory record not found.")
        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(inventory, field, value)
        return await self.repo.save(inventory)

    async def list_transactions(
        self,
        inventory_id: str | None = None,
        warehouse_id: str | None = None,
        product_id: str | None = None,
        transaction_type: InventoryTransactionType | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[InventoryTransaction], int]:
        items = await self.transaction_repo.list(inventory_id, warehouse_id, product_id, transaction_type, limit=limit, offset=offset)
        total = await self.transaction_repo.count(inventory_id, warehouse_id, product_id, transaction_type)
        return items, total
