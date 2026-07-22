from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.batch import Batch, BatchStatus
from app.repositories.batch_repository import BatchRepository
from app.repositories.inventory_repository import InventoryRepository


class BatchService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = BatchRepository(session, organization_id, is_superuser)
        self.inventory_repo = InventoryRepository(session, organization_id, is_superuser)

    async def _ensure_unique_number(self, product_id: str, warehouse_id: str, batch_number: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_number(product_id, warehouse_id, batch_number)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A batch with that number already exists for this product/warehouse.")

    async def create_batch(self, data) -> Batch:
        await self._ensure_unique_number(data.product_id, data.warehouse_id, data.batch_number)
        inventory = await self.inventory_repo.get_or_create_for_update(data.product_id, data.variant_id, data.warehouse_id)
        await self.session.commit()

        batch = Batch(
            inventory_id=inventory.id,
            product_id=data.product_id,
            variant_id=data.variant_id,
            warehouse_id=data.warehouse_id,
            batch_number=data.batch_number,
            manufactured_date=data.manufactured_date,
            expiry_date=data.expiry_date,
            received_quantity=data.received_quantity,
            remaining_quantity=data.received_quantity,
            cost_price=data.cost_price,
            status=BatchStatus(data.status.value),
        )
        return await self.repo.create(batch)

    async def get_or_create_batch(
        self,
        inventory_id: str,
        product_id: str,
        variant_id: str | None,
        warehouse_id: str,
        batch_number: str,
        quantity: int,
        expiry_date: datetime | None = None,
        manufactured_date: datetime | None = None,
        cost_price: float | None = None,
    ) -> Batch:
        """Used by orchestration flows (Goods Receipt) — never commits, caller
        owns the transaction boundary."""
        existing = await self.repo.get_by_number(product_id, warehouse_id, batch_number)
        if existing:
            existing.received_quantity += quantity
            existing.remaining_quantity += quantity
            return await self.repo.save_no_commit(existing)

        batch = Batch(
            inventory_id=inventory_id,
            product_id=product_id,
            variant_id=variant_id,
            warehouse_id=warehouse_id,
            batch_number=batch_number,
            manufactured_date=manufactured_date,
            expiry_date=expiry_date,
            received_quantity=quantity,
            remaining_quantity=quantity,
            cost_price=cost_price,
            status=BatchStatus.active,
        )
        return await self.repo.create_no_commit(batch)

    async def update_batch(self, batch_id: str, data) -> Batch:
        batch = await self.repo.get_by_id(batch_id)
        if not batch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found.")

        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            if field == "status" and value is not None:
                value = BatchStatus(value.value if hasattr(value, "value") else value)
            setattr(batch, field, value)

        return await self.repo.save(batch)

    async def delete_batch(self, batch_id: str) -> None:
        batch = await self.repo.get_by_id(batch_id)
        if not batch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found.")
        await self.repo.soft_delete(batch_id)

    async def get_batch(self, batch_id: str) -> Batch | None:
        return await self.repo.get_by_id(batch_id)

    async def list_batches(
        self,
        product_id: str | None = None,
        warehouse_id: str | None = None,
        status_filter: BatchStatus | None = None,
        expiring_before: datetime | None = None,
        q: str | None = None,
        sort_by: str = "expiry_date",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Batch], int]:
        items = await self.repo.list(product_id, warehouse_id, status_filter, expiring_before, q, sort_by, sort_order, limit, offset)
        total = await self.repo.count(product_id, warehouse_id, status_filter, expiring_before, q)
        return items, total
