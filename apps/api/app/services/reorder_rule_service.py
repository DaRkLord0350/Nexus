from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reorder_rule import ReorderRule
from app.repositories.reorder_rule_repository import ReorderRuleRepository


class ReorderRuleService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = ReorderRuleRepository(session, organization_id, is_superuser)

    async def _ensure_unique_grain(self, product_id: str, variant_id: str | None, warehouse_id: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_grain(product_id, variant_id, warehouse_id)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A reorder rule already exists for this product/variant/warehouse.")

    async def create_rule(self, data) -> ReorderRule:
        await self._ensure_unique_grain(data.product_id, data.variant_id, data.warehouse_id)
        rule = ReorderRule(
            product_id=data.product_id,
            variant_id=data.variant_id,
            warehouse_id=data.warehouse_id,
            minimum_stock=data.minimum_stock,
            maximum_stock=data.maximum_stock,
            reorder_quantity=data.reorder_quantity,
            supplier_name=data.supplier_name,
            lead_time_days=data.lead_time_days,
            is_active=data.is_active,
        )
        return await self.repo.create(rule)

    async def update_rule(self, rule_id: str, data) -> ReorderRule:
        rule = await self.repo.get_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reorder rule not found.")
        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(rule, field, value)
        return await self.repo.save(rule)

    async def delete_rule(self, rule_id: str) -> None:
        rule = await self.repo.get_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reorder rule not found.")
        await self.repo.soft_delete(rule_id)

    async def bulk_delete(self, rule_ids: list[str]) -> int:
        deleted = 0
        for rule_id in rule_ids:
            rule = await self.repo.get_by_id(rule_id)
            if rule:
                await self.repo.soft_delete(rule_id)
                deleted += 1
        return deleted

    async def get_rule(self, rule_id: str) -> ReorderRule | None:
        return await self.repo.get_by_id(rule_id)

    async def list_rules(
        self,
        warehouse_id: str | None = None,
        product_id: str | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ReorderRule], int]:
        items = await self.repo.list(warehouse_id, product_id, is_active, limit, offset)
        total = await self.repo.count(warehouse_id, product_id, is_active)
        return items, total
