from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete as sa_delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attribute_value import AttributeValue
from app.models.variant import Variant, VariantStatus
from app.models.variant_attribute_value import VariantAttributeValue
from app.repositories.base_repository import BaseRepository

SORTABLE_FIELDS = {
    "sku": Variant.sku,
    "sort_order": Variant.sort_order,
    "created_at": Variant.created_at,
}


class VariantRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, variant: Variant) -> Variant:
        self._add_tenant_on_create(variant)
        self.session.add(variant)
        await self.session.commit()
        await self.session.refresh(variant)
        return variant

    async def save(self, variant: Variant) -> Variant:
        self.session.add(variant)
        await self.session.commit()
        await self.session.refresh(variant)
        return variant

    async def get_by_id(self, variant_id: str) -> Variant | None:
        statement = select(Variant).where(Variant.id == variant_id)
        statement = self._apply_tenant_filter(statement, Variant)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str) -> Variant | None:
        statement = select(Variant).where(Variant.sku == sku)
        statement = self._apply_tenant_filter(statement, Variant)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(self, statement, status: VariantStatus | None = None, q: str | None = None):
        if status is not None:
            statement = statement.where(Variant.status == status)
        if q:
            like = f"%{q}%"
            statement = statement.where(or_(Variant.sku.ilike(like), Variant.barcode.ilike(like)))
        return statement

    async def list_for_product(
        self,
        product_id: str,
        status: VariantStatus | None = None,
        q: str | None = None,
        sort_by: str = "sort_order",
        sort_order: str = "asc",
        limit: int = 100,
        offset: int = 0,
    ) -> list[Variant]:
        column = SORTABLE_FIELDS.get(sort_by, Variant.sort_order)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(Variant).where(Variant.product_id == product_id).order_by(order_clause).limit(limit).offset(offset)
        statement = self._apply_filters(statement, status, q)
        statement = self._apply_tenant_filter(statement, Variant)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count_for_product(self, product_id: str, status: VariantStatus | None = None, q: str | None = None) -> int:
        statement = select(func.count(Variant.id)).where(Variant.product_id == product_id)
        statement = self._apply_filters(statement, status, q)
        statement = self._apply_tenant_filter(statement, Variant)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def unset_default_for_product(self, product_id: str, exclude_variant_id: str | None = None) -> None:
        statement = update(Variant).where(Variant.product_id == product_id, Variant.is_default.is_(True)).values(is_default=False)
        if exclude_variant_id:
            statement = statement.where(Variant.id != exclude_variant_id)
        statement = self._apply_tenant_filter(statement, Variant)
        await self.session.execute(statement)

    async def soft_delete(self, variant_id: str) -> None:
        statement = update(Variant).where(Variant.id == variant_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Variant)
        await self.session.execute(statement)
        await self.session.commit()

    async def bulk_soft_delete(self, variant_ids: list[str]) -> int:
        if not variant_ids:
            return 0
        statement = update(Variant).where(Variant.id.in_(variant_ids)).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Variant)
        result = await self.session.execute(statement)
        await self.session.commit()
        return result.rowcount or 0

    # ------------------------------------------------------------------
    # Attribute value links
    # ------------------------------------------------------------------
    async def set_attribute_values(self, variant_id: str, attribute_value_ids: list[str]) -> None:
        statement = sa_delete(VariantAttributeValue).where(VariantAttributeValue.variant_id == variant_id)
        await self.session.execute(statement)
        for attribute_value_id in attribute_value_ids:
            link = VariantAttributeValue(variant_id=variant_id, attribute_value_id=attribute_value_id)
            self._add_tenant_on_create(link)
            self.session.add(link)
        await self.session.commit()

    async def get_attribute_values(self, variant_id: str) -> list[AttributeValue]:
        statement = (
            select(AttributeValue)
            .join(VariantAttributeValue, VariantAttributeValue.attribute_value_id == AttributeValue.id)
            .where(VariantAttributeValue.variant_id == variant_id)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_attribute_values_for_variants(self, variant_ids: list[str]) -> dict[str, list[AttributeValue]]:
        if not variant_ids:
            return {}
        statement = (
            select(VariantAttributeValue.variant_id, AttributeValue)
            .join(AttributeValue, VariantAttributeValue.attribute_value_id == AttributeValue.id)
            .where(VariantAttributeValue.variant_id.in_(variant_ids))
        )
        result = await self.session.execute(statement)
        grouped: dict[str, list[AttributeValue]] = {variant_id: [] for variant_id in variant_ids}
        for variant_id, attribute_value in result.all():
            grouped[variant_id].append(attribute_value)
        return grouped
