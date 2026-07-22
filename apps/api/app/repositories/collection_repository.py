from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete as sa_delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection import Collection, CollectionStatus
from app.models.collection_product import CollectionProduct
from app.models.product import Product
from app.repositories.base_repository import BaseRepository

SORTABLE_FIELDS = {
    "name": Collection.name,
    "sort_order": Collection.sort_order,
    "created_at": Collection.created_at,
}


class CollectionRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, collection: Collection) -> Collection:
        self._add_tenant_on_create(collection)
        self.session.add(collection)
        await self.session.commit()
        await self.session.refresh(collection)
        return collection

    async def save(self, collection: Collection) -> Collection:
        self.session.add(collection)
        await self.session.commit()
        await self.session.refresh(collection)
        return collection

    async def get_by_id(self, collection_id: str) -> Collection | None:
        statement = select(Collection).where(Collection.id == collection_id)
        statement = self._apply_tenant_filter(statement, Collection)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Collection | None:
        statement = select(Collection).where(Collection.slug == slug)
        statement = self._apply_tenant_filter(statement, Collection)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(self, statement, status: CollectionStatus | None = None, is_featured: bool | None = None, q: str | None = None):
        if status is not None:
            statement = statement.where(Collection.status == status)
        if is_featured is not None:
            statement = statement.where(Collection.is_featured == is_featured)
        if q:
            like = f"%{q}%"
            statement = statement.where(or_(Collection.name.ilike(like), Collection.slug.ilike(like)))
        return statement

    async def list(
        self,
        status: CollectionStatus | None = None,
        is_featured: bool | None = None,
        q: str | None = None,
        sort_by: str = "sort_order",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Collection]:
        column = SORTABLE_FIELDS.get(sort_by, Collection.sort_order)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(Collection).order_by(order_clause).limit(limit).offset(offset)
        statement = self._apply_filters(statement, status, is_featured, q)
        statement = self._apply_tenant_filter(statement, Collection)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, status: CollectionStatus | None = None, is_featured: bool | None = None, q: str | None = None) -> int:
        statement = select(func.count(Collection.id))
        statement = self._apply_filters(statement, status, is_featured, q)
        statement = self._apply_tenant_filter(statement, Collection)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def get_by_id_including_deleted(self, collection_id: str) -> Collection | None:
        statement = select(Collection).where(Collection.id == collection_id)
        if not self.is_superuser and self.organization_id is not None:
            statement = statement.where(Collection.organization_id == self.organization_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def soft_delete(self, collection_id: str) -> None:
        statement = update(Collection).where(Collection.id == collection_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Collection)
        await self.session.execute(statement)
        await self.session.commit()

    async def restore(self, collection_id: str) -> Collection | None:
        statement = update(Collection).where(Collection.id == collection_id).values(deleted_at=None)
        if not self.is_superuser and self.organization_id is not None:
            statement = statement.where(Collection.organization_id == self.organization_id)
        await self.session.execute(statement)
        await self.session.commit()
        return await self.get_by_id(collection_id)

    async def bulk_soft_delete(self, collection_ids: list[str]) -> int:
        if not collection_ids:
            return 0
        statement = update(Collection).where(Collection.id.in_(collection_ids)).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Collection)
        result = await self.session.execute(statement)
        await self.session.commit()
        return result.rowcount or 0

    # ------------------------------------------------------------------
    # Manual membership
    # ------------------------------------------------------------------
    async def add_products(self, collection_id: str, product_ids: list[str]) -> None:
        existing_statement = select(CollectionProduct.product_id).where(CollectionProduct.collection_id == collection_id)
        existing = {row[0] for row in (await self.session.execute(existing_statement)).all()}
        max_sort_statement = select(func.max(CollectionProduct.sort_order)).where(CollectionProduct.collection_id == collection_id)
        next_sort = ((await self.session.execute(max_sort_statement)).scalar_one() or 0) + 1

        for product_id in product_ids:
            if product_id in existing:
                continue
            link = CollectionProduct(collection_id=collection_id, product_id=product_id, sort_order=next_sort)
            self._add_tenant_on_create(link)
            self.session.add(link)
            next_sort += 1
        await self.session.commit()

    async def remove_products(self, collection_id: str, product_ids: list[str]) -> None:
        statement = sa_delete(CollectionProduct).where(
            CollectionProduct.collection_id == collection_id, CollectionProduct.product_id.in_(product_ids)
        )
        await self.session.execute(statement)
        await self.session.commit()

    async def reorder_products(self, collection_id: str, product_ids: list[str]) -> None:
        for index, product_id in enumerate(product_ids):
            statement = (
                update(CollectionProduct)
                .where(CollectionProduct.collection_id == collection_id, CollectionProduct.product_id == product_id)
                .values(sort_order=index)
            )
            await self.session.execute(statement)
        await self.session.commit()

    async def list_manual_products(self, collection_id: str) -> list[Product]:
        statement = (
            select(Product)
            .join(CollectionProduct, CollectionProduct.product_id == Product.id)
            .where(CollectionProduct.collection_id == collection_id, Product.deleted_at.is_(None))
            .order_by(CollectionProduct.sort_order.asc())
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count_manual_products(self, collection_id: str) -> int:
        statement = select(func.count(CollectionProduct.id)).where(CollectionProduct.collection_id == collection_id)
        result = await self.session.execute(statement)
        return result.scalar_one()
