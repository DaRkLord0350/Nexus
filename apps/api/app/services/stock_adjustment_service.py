from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory_transaction import InventoryTransactionType
from app.models.stock_adjustment import StockAdjustment, StockAdjustmentReason
from app.repositories.stock_adjustment_repository import StockAdjustmentRepository
from app.services.stock_movement_service import StockMovementService


class StockAdjustmentService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = StockAdjustmentRepository(session, organization_id, is_superuser)
        self.movement_service = StockMovementService(session, organization_id, is_superuser)

    async def _ensure_unique_number(self, adjustment_number: str) -> None:
        existing = await self.repo.get_by_number(adjustment_number)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A stock adjustment with that number already exists.")

    async def create_adjustment(self, data, created_by: str | None = None) -> StockAdjustment:
        if data.quantity_delta == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="quantity_delta must be non-zero.")

        adjustment_number = data.adjustment_number or f"ADJ-{uuid4().hex[:8].upper()}"
        await self._ensure_unique_number(adjustment_number)

        transaction = await self.movement_service.apply_movement(
            product_id=data.product_id,
            variant_id=data.variant_id,
            warehouse_id=data.warehouse_id,
            bin_id=data.bin_id,
            transaction_type=InventoryTransactionType.adjustment,
            quantity_delta=data.quantity_delta,
            reference_type="stock_adjustment",
            user_id=created_by,
            notes=data.notes,
        )

        adjustment = StockAdjustment(
            adjustment_number=adjustment_number,
            inventory_id=transaction.inventory_id,
            product_id=data.product_id,
            variant_id=data.variant_id,
            warehouse_id=data.warehouse_id,
            bin_id=data.bin_id,
            quantity_delta=data.quantity_delta,
            reason=StockAdjustmentReason(data.reason.value),
            notes=data.notes,
            created_by=created_by,
        )
        adjustment = await self.repo.create(adjustment)

        # Backfill the transaction's reference_id now that the adjustment
        # row exists (the transaction is created first since it needs to
        # resolve/create the Inventory row that the adjustment FKs to).
        transaction.reference_id = adjustment.id
        self.session.add(transaction)
        await self.session.commit()

        return adjustment

    async def get_adjustment(self, adjustment_id: str) -> StockAdjustment | None:
        return await self.repo.get_by_id(adjustment_id)

    async def list_adjustments(
        self,
        warehouse_id: str | None = None,
        product_id: str | None = None,
        reason: StockAdjustmentReason | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[StockAdjustment], int]:
        items = await self.repo.list(warehouse_id, product_id, reason, limit, offset)
        total = await self.repo.count(warehouse_id, product_id, reason)
        return items, total
