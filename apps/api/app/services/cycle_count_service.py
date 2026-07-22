from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cycle_count import CycleCount, CycleCountStatus
from app.models.cycle_count_item import CycleCountItem
from app.models.inventory_transaction import InventoryTransactionType
from app.repositories.cycle_count_repository import CycleCountItemRepository, CycleCountRepository
from app.repositories.inventory_repository import InventoryRepository
from app.services.stock_movement_service import StockMovementService


class CycleCountService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = CycleCountRepository(session, organization_id, is_superuser)
        self.item_repo = CycleCountItemRepository(session, organization_id, is_superuser)
        self.inventory_repo = InventoryRepository(session, organization_id, is_superuser)
        self.movement_service = StockMovementService(session, organization_id, is_superuser)

    async def _ensure_unique_number(self, count_number: str) -> None:
        existing = await self.repo.get_by_number(count_number)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A cycle count with that number already exists.")

    async def create_cycle_count(self, data) -> CycleCount:
        count_number = data.count_number or f"CC-{uuid4().hex[:8].upper()}"
        await self._ensure_unique_number(count_number)

        cycle_count = CycleCount(
            count_number=count_number,
            warehouse_id=data.warehouse_id,
            zone_id=data.zone_id,
            scheduled_date=data.scheduled_date,
            assigned_to=data.assigned_to,
            notes=data.notes,
        )
        cycle_count = await self.repo.create(cycle_count)

        for item_data in data.items:
            inventory = await self.inventory_repo.get_or_create_for_update(item_data.product_id, item_data.variant_id, data.warehouse_id, item_data.bin_id)
            await self.session.commit()

            item = CycleCountItem(
                cycle_count_id=cycle_count.id,
                inventory_id=inventory.id,
                product_id=item_data.product_id,
                variant_id=item_data.variant_id,
                bin_id=item_data.bin_id,
                expected_quantity=inventory.quantity_available,
                notes=item_data.notes,
            )
            await self.item_repo.create(item)

        return cycle_count

    async def _get_or_404(self, cycle_count_id: str) -> CycleCount:
        cycle_count = await self.repo.get_by_id(cycle_count_id)
        if not cycle_count:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cycle count not found.")
        return cycle_count

    async def record_count(self, cycle_count_id: str, item_id: str, data, counted_by: str | None = None) -> CycleCountItem:
        cycle_count = await self._get_or_404(cycle_count_id)
        if cycle_count.status not in (CycleCountStatus.scheduled, CycleCountStatus.in_progress):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Counts can only be recorded on scheduled or in-progress cycle counts.")

        item = await self.item_repo.get_by_id(item_id)
        if not item or item.cycle_count_id != cycle_count_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cycle count item not found.")

        item.actual_quantity = data.actual_quantity
        item.variance = data.actual_quantity - item.expected_quantity
        item.counted_at = datetime.utcnow()
        item.counted_by = counted_by
        if data.notes is not None:
            item.notes = data.notes
        item = await self.item_repo.save(item)

        if cycle_count.status == CycleCountStatus.scheduled:
            cycle_count.status = CycleCountStatus.in_progress
            cycle_count.started_at = datetime.utcnow()
            await self.repo.save(cycle_count)

        return item

    async def complete_count(self, cycle_count_id: str, user_id: str | None) -> CycleCount:
        """Orchestration entry point: for every counted item whose actual
        quantity differs from expected, applies the variance via
        StockMovementService (type=cycle_count) so the resulting
        Inventory.quantity_available matches what was physically counted."""
        cycle_count = await self._get_or_404(cycle_count_id)
        if cycle_count.status not in (CycleCountStatus.scheduled, CycleCountStatus.in_progress):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only scheduled or in-progress cycle counts can be completed.")

        items = await self.item_repo.list_for_count(cycle_count_id)
        uncounted = [item for item in items if item.actual_quantity is None]
        if uncounted:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="All items must be counted before completing the cycle count.")

        for item in items:
            if item.variance:
                await self.movement_service.apply_movement(
                    product_id=item.product_id,
                    variant_id=item.variant_id,
                    warehouse_id=cycle_count.warehouse_id,
                    bin_id=item.bin_id,
                    transaction_type=InventoryTransactionType.cycle_count,
                    quantity_delta=item.variance,
                    reference_type="cycle_count",
                    reference_id=cycle_count.id,
                    user_id=user_id,
                    allow_negative=True,
                )

        cycle_count.status = CycleCountStatus.completed
        cycle_count.completed_at = datetime.utcnow()
        return await self.repo.save(cycle_count)

    async def cancel_cycle_count(self, cycle_count_id: str) -> CycleCount:
        cycle_count = await self._get_or_404(cycle_count_id)
        if cycle_count.status == CycleCountStatus.completed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel a completed cycle count.")
        cycle_count.status = CycleCountStatus.cancelled
        return await self.repo.save(cycle_count)

    async def get_cycle_count(self, cycle_count_id: str) -> CycleCount | None:
        return await self.repo.get_by_id(cycle_count_id)

    async def get_items(self, cycle_count_id: str) -> list[CycleCountItem]:
        return await self.item_repo.list_for_count(cycle_count_id)

    async def list_cycle_counts(
        self,
        warehouse_id: str | None = None,
        status_filter: CycleCountStatus | None = None,
        q: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[CycleCount], int]:
        items = await self.repo.list(warehouse_id, status_filter, q, limit, offset)
        total = await self.repo.count(warehouse_id, status_filter, q)
        return items, total
