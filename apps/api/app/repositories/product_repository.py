from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, ProductStatus
from app.models.product_tag import ProductTag
from app.repositories.base_repository import BaseRepository

SORTABLE_FIELDS = {
    "name": Product.name,
    "sku": Product.sku,
    "created_at": Product.created_at,
    "updated_at": Product.updated_at,
    "published_at": Product.published_at,
}


class ProductRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, product: Product) -> Product:
        self._add_tenant_on_create(product)
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def save(self, product: Product) -> Product:
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def get_by_id(self, product_id: str) -> Product | None:
        statement = select(Product).where(Product.id == product_id)
        statement = self._apply_tenant_filter(statement, Product)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Product | None:
        statement = select(Product).where(Product.slug == slug)
        statement = self._apply_tenant_filter(statement, Product)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str) -> Product | None:
        statement = select(Product).where(Product.sku == sku)
        statement = self._apply_tenant_filter(statement, Product)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(
        self,
        statement,
        status: ProductStatus | None = None,
        brand_id: str | None = None,
        category_id: str | None = None,
        is_featured: bool | None = None,
        has_variants: bool | None = None,
        q: str | None = None,
        tag_id: str | None = None,
    ):
        if status is not None:
            statement = statement.where(Product.status == status)
        if brand_id is not None:
            statement = statement.where(Product.brand_id == brand_id)
        if category_id is not None:
            statement = statement.where(Product.category_id == category_id)
        if is_featured is not None:
            statement = statement.where(Product.is_featured == is_featured)
        if has_variants is not None:
            statement = statement.where(Product.has_variants == has_variants)
        if q:
            like = f"%{q}%"
            statement = statement.where(
                or_(Product.name.ilike(like), Product.sku.ilike(like), Product.barcode.ilike(like), Product.slug.ilike(like))
            )
        if tag_id is not None:
            statement = statement.where(Product.id.in_(select(ProductTag.product_id).where(ProductTag.tag_id == tag_id)))
        return statement

    async def list(
        self,
        status: ProductStatus | None = None,
        brand_id: str | None = None,
        category_id: str | None = None,
        is_featured: bool | None = None,
        has_variants: bool | None = None,
        q: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
        tag_id: str | None = None,
    ) -> list[Product]:
        column = SORTABLE_FIELDS.get(sort_by, Product.created_at)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(Product).order_by(order_clause).limit(limit).offset(offset)
        statement = self._apply_filters(statement, status, brand_id, category_id, is_featured, has_variants, q, tag_id)
        statement = self._apply_tenant_filter(statement, Product)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(
        self,
        status: ProductStatus | None = None,
        brand_id: str | None = None,
        category_id: str | None = None,
        is_featured: bool | None = None,
        has_variants: bool | None = None,
        q: str | None = None,
        tag_id: str | None = None,
    ) -> int:
        statement = select(func.count(Product.id))
        statement = self._apply_filters(statement, status, brand_id, category_id, is_featured, has_variants, q, tag_id)
        statement = self._apply_tenant_filter(statement, Product)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def get_by_id_including_deleted(self, product_id: str) -> Product | None:
        statement = select(Product).where(Product.id == product_id)
        if not self.is_superuser and self.organization_id is not None:
            statement = statement.where(Product.organization_id == self.organization_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def soft_delete(self, product_id: str) -> None:
        statement = update(Product).where(Product.id == product_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Product)
        await self.session.execute(statement)
        await self.session.commit()

    async def restore(self, product_id: str) -> Product | None:
        statement = update(Product).where(Product.id == product_id).values(deleted_at=None)
        if not self.is_superuser and self.organization_id is not None:
            statement = statement.where(Product.organization_id == self.organization_id)
        await self.session.execute(statement)
        await self.session.commit()
        return await self.get_by_id(product_id)

    async def bulk_soft_delete(self, product_ids: list[str]) -> int:
        if not product_ids:
            return 0
        statement = update(Product).where(Product.id.in_(product_ids)).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Product)
        result = await self.session.execute(statement)
        await self.session.commit()
        return result.rowcount or 0

    async def bulk_update_status(self, product_ids: list[str], new_status: ProductStatus) -> int:
        if not product_ids:
            return 0
        values = {"status": new_status}
        if new_status == ProductStatus.published:
            values["published_at"] = datetime.utcnow()
        statement = update(Product).where(Product.id.in_(product_ids)).values(**values)
        statement = self._apply_tenant_filter(statement, Product)
        result = await self.session.execute(statement)
        await self.session.commit()
        return result.rowcount or 0
