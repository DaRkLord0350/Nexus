from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_price import ProductPrice
from app.repositories.base_repository import BaseRepository


class ProductPriceRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, price: ProductPrice) -> ProductPrice:
        self._add_tenant_on_create(price)
        self.session.add(price)
        await self.session.commit()
        await self.session.refresh(price)
        return price

    async def save(self, price: ProductPrice) -> ProductPrice:
        self.session.add(price)
        await self.session.commit()
        await self.session.refresh(price)
        return price

    async def get_by_id(self, price_id: str) -> ProductPrice | None:
        statement = select(ProductPrice).where(ProductPrice.id == price_id)
        statement = self._apply_tenant_filter(statement, ProductPrice)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_product(
        self,
        product_id: str,
        variant_id: str | None = "__unset__",
        currency: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ProductPrice]:
        statement = select(ProductPrice).where(ProductPrice.product_id == product_id).order_by(ProductPrice.created_at.desc()).limit(limit).offset(offset)
        if variant_id != "__unset__":
            statement = statement.where(ProductPrice.variant_id == variant_id) if variant_id is not None else statement.where(ProductPrice.variant_id.is_(None))
        if currency:
            statement = statement.where(ProductPrice.currency == currency)
        statement = self._apply_tenant_filter(statement, ProductPrice)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count_for_product(self, product_id: str, variant_id: str | None = "__unset__", currency: str | None = None) -> int:
        statement = select(func.count(ProductPrice.id)).where(ProductPrice.product_id == product_id)
        if variant_id != "__unset__":
            statement = statement.where(ProductPrice.variant_id == variant_id) if variant_id is not None else statement.where(ProductPrice.variant_id.is_(None))
        if currency:
            statement = statement.where(ProductPrice.currency == currency)
        statement = self._apply_tenant_filter(statement, ProductPrice)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def list_candidates(self, product_id: str, currency: str, at_time: datetime) -> list[ProductPrice]:
        """Active, currently-effective price rows for a product (any variant/scope), for resolution."""
        statement = select(ProductPrice).where(
            ProductPrice.product_id == product_id,
            ProductPrice.currency == currency,
            ProductPrice.is_active.is_(True),
        )
        statement = statement.where((ProductPrice.effective_from.is_(None)) | (ProductPrice.effective_from <= at_time))
        statement = statement.where((ProductPrice.effective_to.is_(None)) | (ProductPrice.effective_to >= at_time))
        statement = self._apply_tenant_filter(statement, ProductPrice)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def soft_delete(self, price_id: str) -> None:
        statement = update(ProductPrice).where(ProductPrice.id == price_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, ProductPrice)
        await self.session.execute(statement)
        await self.session.commit()

    async def bulk_soft_delete(self, price_ids: list[str]) -> int:
        if not price_ids:
            return 0
        statement = update(ProductPrice).where(ProductPrice.id.in_(price_ids)).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, ProductPrice)
        result = await self.session.execute(statement)
        await self.session.commit()
        return result.rowcount or 0
