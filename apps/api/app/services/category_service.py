from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category, CategoryStatus
from app.repositories.category_repository import CategoryRepository
from app.services.slug_redirect_service import SlugRedirectService
from app.utils.text import slugify


class CategoryService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = CategoryRepository(session, organization_id, is_superuser)
        self.slug_redirect_service = SlugRedirectService(session, organization_id, is_superuser)

    async def _resolve_parent(self, parent_id: str | None) -> Category | None:
        if not parent_id:
            return None
        parent = await self.repo.get_by_id(parent_id)
        if not parent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent category not found.")
        return parent

    def _build_path(self, parent: Category | None, slug: str) -> str:
        return f"{parent.path}/{slug}" if parent else slug

    async def _ensure_unique_slug(self, slug: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_slug(slug)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A category with that slug already exists.")

    async def create_category(self, data, created_by: str | None = None) -> Category:
        parent = await self._resolve_parent(data.parent_id)
        slug = slugify(data.slug or data.name, fallback="category")
        await self._ensure_unique_slug(slug)

        category = Category(
            name=data.name,
            slug=slug,
            description=data.description,
            parent_id=parent.id if parent else None,
            path=self._build_path(parent, slug),
            image_url=data.image_url,
            banner_url=data.banner_url,
            sort_order=data.sort_order,
            is_featured=data.is_featured,
            is_visible=data.is_visible,
            status=CategoryStatus(data.status.value),
            seo_title=data.seo_title,
            seo_description=data.seo_description,
            seo_keywords=data.seo_keywords,
            og_image_url=data.og_image_url,
            canonical_url=data.canonical_url,
            no_index=data.no_index,
            created_by=created_by,
        )
        return await self.repo.create(category)

    async def update_category(self, category_id: str, data) -> Category:
        category = await self.repo.get_by_id(category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

        changes = data.model_dump(exclude_unset=True, exclude={"parent_id", "move_to_root", "slug"})
        for field, value in changes.items():
            if field == "status" and value is not None:
                value = CategoryStatus(value.value if hasattr(value, "value") else value)
            setattr(category, field, value)

        new_slug = category.slug
        if data.slug is not None:
            new_slug = slugify(data.slug, fallback="category")
            await self._ensure_unique_slug(new_slug, exclude_id=category.id)
        elif data.name is not None:
            new_slug = slugify(data.name, fallback="category")
            await self._ensure_unique_slug(new_slug, exclude_id=category.id)

        target_parent_id = category.parent_id
        parent_changed = False
        if data.move_to_root:
            target_parent_id = None
            parent_changed = target_parent_id != category.parent_id
        elif data.parent_id is not None:
            if data.parent_id == category.id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A category cannot be its own parent.")
            descendants = await self.repo.list_descendants(category.id)
            if data.parent_id in {d.id for d in descendants}:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A category cannot be moved into its own subcategory.")
            target_parent_id = data.parent_id
            parent_changed = target_parent_id != category.parent_id

        slug_changed = new_slug != category.slug
        if slug_changed or parent_changed:
            parent = await self._resolve_parent(target_parent_id)
            new_path = self._build_path(parent, new_slug)
            await self._reparent_descendant_paths(category, new_path)
            await self.slug_redirect_service.record("category", category.path, new_path)
            category.slug = new_slug
            category.parent_id = target_parent_id
            category.path = new_path

        return await self.repo.save(category)

    async def _reparent_descendant_paths(self, category: Category, new_path: str) -> None:
        old_prefix = category.path
        descendants = await self.repo.list_descendants(category.id)
        for descendant in descendants:
            if descendant.path.startswith(old_prefix + "/"):
                await self.repo.update_path(descendant.id, new_path + descendant.path[len(old_prefix):])
        if descendants:
            await self.session.commit()

    async def delete_category(self, category_id: str, cascade: bool = False) -> None:
        category = await self.repo.get_by_id(category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

        child_count = await self.repo.count_children(category_id)
        if child_count and not cascade:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category has subcategories. Pass cascade=true to delete them too.")

        if cascade:
            descendants = await self.repo.list_descendants(category_id)
            for descendant in reversed(descendants):
                await self.repo.soft_delete(descendant.id)
        await self.repo.soft_delete(category_id)

    async def restore_category(self, category_id: str) -> Category:
        category = await self.repo.get_by_id_including_deleted(category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
        if category.deleted_at is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category is not deleted.")
        restored = await self.repo.restore(category_id)
        return restored

    async def get_category(self, category_id: str) -> Category | None:
        return await self.repo.get_by_id(category_id)

    async def get_by_slug(self, slug: str) -> Category | None:
        return await self.repo.get_by_slug(slug)

    async def list_categories(
        self,
        parent_id: str | None = "__unset__",
        status_filter: CategoryStatus | None = None,
        is_featured: bool | None = None,
        is_visible: bool | None = None,
        q: str | None = None,
        sort_by: str = "sort_order",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Category], int]:
        items = await self.repo.list(parent_id, status_filter, is_featured, is_visible, q, sort_by, sort_order, limit, offset)
        total = await self.repo.count(parent_id, status_filter, is_featured, is_visible, q)
        return items, total

    async def get_tree(self, parent_id: str | None = None) -> list[dict]:
        children = await self.repo.list_children(parent_id)
        tree = []
        for child in children:
            tree.append({
                "id": child.id,
                "name": child.name,
                "slug": child.slug,
                "description": child.description,
                "parent_id": child.parent_id,
                "path": child.path,
                "image_url": child.image_url,
                "banner_url": child.banner_url,
                "sort_order": child.sort_order,
                "is_featured": child.is_featured,
                "is_visible": child.is_visible,
                "status": child.status,
                "seo_title": child.seo_title,
                "seo_description": child.seo_description,
                "seo_keywords": child.seo_keywords,
                "created_at": child.created_at,
                "updated_at": child.updated_at,
                "children": await self.get_tree(child.id),
            })
        return tree

    async def get_breadcrumbs(self, category_id: str) -> list[Category]:
        trail: list[Category] = []
        current_id: str | None = category_id
        visited: set[str] = set()
        while current_id and current_id not in visited:
            visited.add(current_id)
            category = await self.repo.get_by_id(current_id)
            if not category:
                break
            trail.append(category)
            current_id = category.parent_id
        return list(reversed(trail))
