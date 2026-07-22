from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory_transaction import InventoryTransaction, InventoryTransactionType
from app.models.notification import NotificationType
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.inventory_transaction_repository import InventoryTransactionRepository
from app.repositories.reorder_rule_repository import ReorderRuleRepository
from app.repositories.user_repository import UserRepository
from app.services.notification_service import NotificationService
from app.services.permission_service import PermissionService

MUTABLE_QUANTITY_FIELDS = {
    "quantity_available",
    "quantity_reserved",
    "quantity_incoming",
    "quantity_damaged",
    "quantity_returned",
}

LOW_STOCK_NOTIFICATION_COOLDOWN = timedelta(hours=24)


class StockMovementService:
    """The single write path for Inventory.quantity_* columns. Every module
    that moves stock (adjustments, transfers, goods receipt, cycle counts,
    reorder rules) calls apply_movement() instead of touching the Inventory
    row directly, so every quantity change is always paired with an
    InventoryTransaction audit row inside one commit."""

    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.inventory_repo = InventoryRepository(session, organization_id, is_superuser)
        self.transaction_repo = InventoryTransactionRepository(session, organization_id, is_superuser)

    async def apply_movement(
        self,
        *,
        product_id: str,
        variant_id: str | None,
        warehouse_id: str,
        transaction_type: InventoryTransactionType,
        quantity_delta: int,
        field: str = "quantity_available",
        bin_id: str | None = None,
        batch_id: str | None = None,
        serial_number_id: str | None = None,
        reference_type: str | None = None,
        reference_id: str | None = None,
        user_id: str | None = None,
        notes: str | None = None,
        allow_negative: bool = False,
    ) -> InventoryTransaction:
        if field not in MUTABLE_QUANTITY_FIELDS:
            raise ValueError(f"Unsupported inventory field: {field}")

        inventory = await self.inventory_repo.get_or_create_for_update(product_id, variant_id, warehouse_id, bin_id)
        if bin_id and not inventory.bin_id:
            inventory.bin_id = bin_id

        quantity_before = getattr(inventory, field)
        quantity_after = quantity_before + quantity_delta
        if quantity_after < 0 and not allow_negative:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This movement would take {field} below zero ({quantity_before} -> {quantity_after}).",
            )

        setattr(inventory, field, quantity_after)
        await self.inventory_repo.save_no_commit(inventory)

        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            product_id=product_id,
            variant_id=variant_id,
            warehouse_id=warehouse_id,
            batch_id=batch_id,
            serial_number_id=serial_number_id,
            type=transaction_type,
            quantity=quantity_delta,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            reference_type=reference_type,
            reference_id=reference_id,
            user_id=user_id,
            notes=notes,
            occurred_at=datetime.utcnow(),
        )
        await self.transaction_repo.create_no_commit(transaction)

        if field == "quantity_available" and quantity_delta < 0:
            await self._maybe_notify_low_stock(inventory)

        await self.session.commit()
        await self.session.refresh(transaction)
        return transaction

    async def _maybe_notify_low_stock(self, inventory) -> None:
        if inventory.reorder_point is None or inventory.quantity_available > inventory.reorder_point:
            return

        now = datetime.utcnow()
        if inventory.low_stock_notified_at and now - inventory.low_stock_notified_at < LOW_STOCK_NOTIFICATION_COOLDOWN:
            return

        inventory.low_stock_notified_at = now
        await self.inventory_repo.save_no_commit(inventory)

        metadata = {
            "inventory_id": inventory.id,
            "product_id": inventory.product_id,
            "variant_id": inventory.variant_id,
            "warehouse_id": inventory.warehouse_id,
            "quantity_available": inventory.quantity_available,
            "reorder_point": inventory.reorder_point,
        }
        message = (
            f"Product {inventory.product_id} at warehouse {inventory.warehouse_id} is at "
            f"{inventory.quantity_available} units, at or below its reorder point of {inventory.reorder_point}."
        )

        rule_repo = ReorderRuleRepository(self.session, self.organization_id, self.is_superuser)
        rule = await rule_repo.get_by_grain(inventory.product_id, inventory.variant_id, inventory.warehouse_id)
        if rule and rule.is_active:
            rule.last_triggered_at = now
            await rule_repo.save_no_commit(rule)
            metadata.update({
                "reorder_rule_id": rule.id,
                "suggested_reorder_quantity": rule.reorder_quantity,
                "supplier_name": rule.supplier_name,
                "lead_time_days": rule.lead_time_days,
            })
            message += f" Suggested reorder: {rule.reorder_quantity} units"
            if rule.supplier_name:
                message += f" from {rule.supplier_name}"
            message += "."

        # Recipients are users holding inventory.reorder_rules.manage; if none
        # are configured yet (org hasn't assigned that permission to anyone),
        # fall back to notifying every active org user so the alert isn't
        # silently dropped.
        permission_service = PermissionService(self.session, self.organization_id, self.is_superuser)
        recipient_ids = await permission_service.list_user_ids_with_permission("inventory.reorder_rules.manage")
        if not recipient_ids:
            user_repo = UserRepository(self.session, self.organization_id, self.is_superuser)
            recipients = await user_repo.list_for_organization(limit=200)
            recipient_ids = [recipient.id for recipient in recipients if recipient.is_active]

        notification_service = NotificationService(self.session, self.organization_id, self.is_superuser)
        for recipient_id in recipient_ids:
            await notification_service.send_notification(
                user_id=recipient_id,
                title="Low stock alert",
                message=message,
                notification_type=NotificationType.warning,
                metadata=metadata,
            )
