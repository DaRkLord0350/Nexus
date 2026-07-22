from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.variant import Variant, VariantStatus
from app.repositories.attribute_value_repository import AttributeValueRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.variant_repository import VariantRepository


class VariantService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = VariantRepository(session, organization_id, is_superuser)
        self.product_repo = ProductRepository(session, organization_id, is_superuser)
        self.attribute_value_repo = AttributeValueRepository(session, organization_id, is_superuser)

    async def _ensure_product_exists(self, product_id: str):
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        return product

    async def _ensure_unique_sku(self, sku: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_sku(sku)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A variant with that SKU already exists.")

    async def _validate_attribute_values(self, attribute_value_ids: list[str]) -> None:
        if not attribute_value_ids:
            return
        found = await self.attribute_value_repo.list_by_ids(attribute_value_ids)
        if len(found) != len(set(attribute_value_ids)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more attribute values were not found.")

    async def _enrich(self, variant: Variant) -> Variant:
        variant.attribute_values = await self.repo.get_attribute_values(variant.id)
        return variant

    async def _enrich_many(self, variants: list[Variant]) -> list[Variant]:
        grouped = await self.repo.get_attribute_values_for_variants([v.id for v in variants])
        for variant in variants:
            variant.attribute_values = grouped.get(variant.id, [])
        return variants

    async def create_variant(self, product_id: str, data, created_by: str | None = None) -> Variant:
        product = await self._ensure_product_exists(product_id)
        await self._ensure_unique_sku(data.sku)
        await self._validate_attribute_values(data.attribute_value_ids)

        variant = Variant(
            product_id=product_id,
            sku=data.sku,
            barcode=data.barcode,
            weight=data.weight,
            weight_unit=data.weight_unit,
            status=VariantStatus(data.status.value),
            is_default=data.is_default,
            sort_order=data.sort_order,
            created_by=created_by,
        )
        created = await self.repo.create(variant)

        if data.attribute_value_ids:
            await self.repo.set_attribute_values(created.id, data.attribute_value_ids)

        if created.is_default:
            await self.repo.unset_default_for_product(product_id, exclude_variant_id=created.id)
            await self.session.commit()

        if not product.has_variants:
            product.has_variants = True
            await self.product_repo.save(product)

        return await self._enrich(created)

    async def update_variant(self, variant_id: str, data) -> Variant:
        variant = await self.repo.get_by_id(variant_id)
        if not variant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found.")

        if data.sku is not None:
            await self._ensure_unique_sku(data.sku, exclude_id=variant.id)

        if data.attribute_value_ids is not None:
            await self._validate_attribute_values(data.attribute_value_ids)

        changes = data.model_dump(exclude_unset=True, exclude={"attribute_value_ids"})
        for field, value in changes.items():
            if field == "status" and value is not None:
                value = VariantStatus(value.value if hasattr(value, "value") else value)
            setattr(variant, field, value)

        saved = await self.repo.save(variant)

        if data.attribute_value_ids is not None:
            await self.repo.set_attribute_values(variant_id, data.attribute_value_ids)

        if saved.is_default:
            await self.repo.unset_default_for_product(saved.product_id, exclude_variant_id=saved.id)
            await self.session.commit()

        return await self._enrich(saved)

    async def set_default_variant(self, variant_id: str) -> Variant:
        variant = await self.repo.get_by_id(variant_id)
        if not variant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found.")
        variant.is_default = True
        saved = await self.repo.save(variant)
        await self.repo.unset_default_for_product(saved.product_id, exclude_variant_id=saved.id)
        await self.session.commit()
        return await self._enrich(saved)

    async def delete_variant(self, variant_id: str) -> None:
        variant = await self.repo.get_by_id(variant_id)
        if not variant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found.")
        await self.repo.soft_delete(variant_id)

    async def bulk_delete(self, variant_ids: list[str]) -> int:
        return await self.repo.bulk_soft_delete(variant_ids)

    async def get_variant(self, variant_id: str) -> Variant | None:
        variant = await self.repo.get_by_id(variant_id)
        if not variant:
            return None
        return await self._enrich(variant)

    async def list_variants(
        self,
        product_id: str,
        status_filter: VariantStatus | None = None,
        q: str | None = None,
        sort_by: str = "sort_order",
        sort_order: str = "asc",
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Variant], int]:
        await self._ensure_product_exists(product_id)
        items = await self.repo.list_for_product(product_id, status_filter, q, sort_by, sort_order, limit, offset)
        items = await self._enrich_many(items)
        total = await self.repo.count_for_product(product_id, status_filter, q)
        return items, total
