from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipping_rule import ShippingRule, ShippingRuleActionType, ShippingRuleConditionType
from app.repositories.shipping_rule_repository import ShippingRuleRepository


class ShippingRuleService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = ShippingRuleRepository(session, organization_id, is_superuser)

    async def create_rule(self, data, created_by: str | None = None) -> ShippingRule:
        rule = ShippingRule(
            name=data.name,
            priority=data.priority,
            is_active=data.is_active,
            condition_type=ShippingRuleConditionType(data.condition_type.value),
            condition_value=data.condition_value,
            action_type=ShippingRuleActionType(data.action_type.value),
            action_value=data.action_value,
        )
        return await self.repo.create(rule)

    async def _get_or_404(self, rule_id: str) -> ShippingRule:
        rule = await self.repo.get_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipping rule not found.")
        return rule

    async def get_rule(self, rule_id: str) -> ShippingRule | None:
        return await self.repo.get_by_id(rule_id)

    async def update_rule(self, rule_id: str, data) -> ShippingRule:
        rule = await self._get_or_404(rule_id)
        changes = data.model_dump(exclude_unset=True)
        if "condition_type" in changes and changes["condition_type"] is not None:
            changes["condition_type"] = ShippingRuleConditionType(changes["condition_type"].value if hasattr(changes["condition_type"], "value") else changes["condition_type"])
        if "action_type" in changes and changes["action_type"] is not None:
            changes["action_type"] = ShippingRuleActionType(changes["action_type"].value if hasattr(changes["action_type"], "value") else changes["action_type"])
        for field, value in changes.items():
            setattr(rule, field, value)
        return await self.repo.save(rule)

    async def delete_rule(self, rule_id: str) -> None:
        await self._get_or_404(rule_id)
        await self.repo.soft_delete(rule_id)

    async def list_rules(self, is_active: bool | None = None, limit: int = 100, offset: int = 0) -> tuple[list[ShippingRule], int]:
        items = await self.repo.list(is_active, limit, offset)
        total = await self.repo.count(is_active)
        return items, total

    def _condition_matches(self, rule: ShippingRule, context) -> bool:
        try:
            if rule.condition_type == ShippingRuleConditionType.weight_greater_than:
                return context.weight > float(rule.condition_value)
            if rule.condition_type == ShippingRuleConditionType.weight_less_than:
                return context.weight < float(rule.condition_value)
            if rule.condition_type == ShippingRuleConditionType.is_cod:
                return context.is_cod == (rule.condition_value.strip().lower() == "true")
            if rule.condition_type == ShippingRuleConditionType.destination_state:
                return bool(context.destination_state) and context.destination_state == rule.condition_value
            if rule.condition_type == ShippingRuleConditionType.destination_country:
                return bool(context.destination_country) and context.destination_country == rule.condition_value
            if rule.condition_type == ShippingRuleConditionType.order_value_greater_than:
                return context.order_value > float(rule.condition_value)
        except (TypeError, ValueError):
            return False
        return False

    async def evaluate(self, context) -> dict:
        rules = await self.repo.list_active_sorted()

        preferred_provider_id = None
        excluded_provider_ids: list[str] = []
        preferred_warehouse_id = None
        matched_rule_ids: list[str] = []

        for rule in rules:
            if not self._condition_matches(rule, context):
                continue

            matched_rule_ids.append(rule.id)
            if rule.action_type == ShippingRuleActionType.assign_provider and preferred_provider_id is None:
                preferred_provider_id = rule.action_value
            elif rule.action_type == ShippingRuleActionType.exclude_provider:
                if rule.action_value not in excluded_provider_ids:
                    excluded_provider_ids.append(rule.action_value)
            elif rule.action_type == ShippingRuleActionType.prefer_warehouse and preferred_warehouse_id is None:
                preferred_warehouse_id = rule.action_value

        return {
            "preferred_provider_id": preferred_provider_id,
            "excluded_provider_ids": excluded_provider_ids,
            "preferred_warehouse_id": preferred_warehouse_id,
            "matched_rule_ids": matched_rule_ids,
        }
