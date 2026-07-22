from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category, CategoryStatus
from app.repositories.base_repository import BaseRepository

SORTABLE_FIELDS = {
    "name": Category.name,
    "sort_order": Category.sort_order,
    "created_at": Category.created_at,
    "updated_at": Category.updated_at,
}


class CategoryRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, category: Category) -> Category:
        self._add_tenant_on_create(category)
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def save(self, category: Category) -> Category:
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def get_by_id(self, category_id: str) -> Category | None:
        statement = select(Category).where(Category.id == category_id)
        statement = self._apply_tenant_filter(statement, Category)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id_including_deleted(self, category_id: str) -> Category | None:
        statement = select(Category).where(Category.id == category_id)
        if not self.is_superuser and self.organization_id is not None:
            statement = statement.where(Category.organization_id == self.organization_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Category | None:
        statement = select(Category).where(Category.slug == slug)
        statement = self._apply_tenant_filter(statement, Category)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(
        self,
        statement,
        parent_id: str | None = "__unset__",
        status: CategoryStatus | None = None,
        is_featured: bool | None = None,
        is_visible: bool | None = None,
        q: str | None = None,
    ):
        if parent_id != "__unset__":
            statement = statement.where(Category.parent_id == parent_id) if parent_id is not None else statement.where(Category.parent_id.is_(None))
        if status is not None:
            statement = statement.where(Category.status == status)
        if is_featured is not None:
            statement = statement.where(Category.is_featured == is_featured)
        if is_visible is not None:
            statement = statement.where(Category.is_visible == is_visible)
        if q:
            like = f"%{q}%"
            statement = statement.where(or_(Category.name.ilike(like), Category.slug.ilike(like)))
        return statement

    async def list(
        self,
        parent_id: str | None = "__unset__",
        status: CategoryStatus | None = None,
        is_featured: bool | None = None,
        is_visible: bool | None = None,
        q: str | None = None,
        sort_by: str = "sort_order",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Category]:
        column = SORTABLE_FIELDS.get(sort_by, Category.sort_order)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(Category).order_by(order_clause).limit(limit).offset(offset)
        statement = self._apply_filters(statement, parent_id, status, is_featured, is_visible, q)
        statement = self._apply_tenant_filter(statement, Category)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(
        self,
        parent_id: str | None = "__unset__",
        status: CategoryStatus | None = None,
        is_featured: bool | None = None,
        is_visible: bool | None = None,
        q: str | None = None,
    ) -> int:
        statement = select(func.count(Category.id))
        statement = self._apply_filters(statement, parent_id, status, is_featured, is_visible, q)
        statement = self._apply_tenant_filter(statement, Category)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def list_children(self, parent_id: str | None) -> list[Category]:
        statement = select(Category).order_by(Category.sort_order.asc(), Category.name.asc())
        statement = statement.where(Category.parent_id == parent_id) if parent_id is not None else statement.where(Category.parent_id.is_(None))
        statement = self._apply_tenant_filter(statement, Category)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def list_descendants(self, category_id: str) -> list[Category]:
        descendants: list[Category] = []
        frontier = [category_id]
        while frontier:
            next_frontier: list[str] = []
            for current_id in frontier:
                children = await self.list_children(current_id)
                descendants.extend(children)
                next_frontier.extend(child.id for child in children)
            frontier = next_frontier
        return descendants

    async def count_children(self, category_id: str) -> int:
        statement = select(func.count(Category.id)).where(Category.parent_id == category_id)
        statement = self._apply_tenant_filter(statement, Category)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def update_path(self, category_id: str, path: str) -> None:
        statement = update(Category).where(Category.id == category_id).values(path=path)
        statement = self._apply_tenant_filter(statement, Category)
        await self.session.execute(statement)

    async def soft_delete(self, category_id: str) -> None:
        statement = update(Category).where(Category.id == category_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Category)
        await self.session.execute(statement)
        await self.session.commit()

    async def restore(self, category_id: str) -> Category | None:
        statement = update(Category).where(Category.id == category_id).values(deleted_at=None)
        if not self.is_superuser and self.organization_id is not None:
            statement = statement.where(Category.organization_id == self.organization_id)
        await self.session.execute(statement)
        await self.session.commit()
        return await self.get_by_id(category_id)
