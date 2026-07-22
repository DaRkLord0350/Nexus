from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection import Collection, CollectionStatus, CollectionType
from app.models.notification import NotificationType
from app.models.product import Product, ProductStatus
from app.repositories.collection_repository import CollectionRepository
from app.repositories.product_repository import ProductRepository
from app.services.notification_service import NotificationService
from app.services.slug_redirect_service import SlugRedirectService
from app.utils.text import slugify

DYNAMIC_RULE_LIMIT = 1000


class CollectionService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = CollectionRepository(session, organization_id, is_superuser)
        self.product_repo = ProductRepository(session, organization_id, is_superuser)
        self.notification_service = NotificationService(session, organization_id, is_superuser)
        self.slug_redirect_service = SlugRedirectService(session, organization_id, is_superuser)

    async def _ensure_unique_slug(self, slug: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_slug(slug)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A collection with that slug already exists.")

    async def create_collection(self, data, created_by: str | None = None) -> Collection:
        slug = slugify(data.slug or data.name, fallback="collection")
        await self._ensure_unique_slug(slug)

        collection = Collection(
            name=data.name,
            slug=slug,
            description=data.description,
            image_url=data.image_url,
            collection_type=CollectionType(data.collection_type.value),
            rules=[rule.model_dump() for rule in data.rules] if data.rules else None,
            status=CollectionStatus(data.status.value),
            is_featured=data.is_featured,
            sort_order=data.sort_order,
            seo_title=data.seo_title,
            seo_description=data.seo_description,
            seo_keywords=data.seo_keywords,
            og_image_url=data.og_image_url,
            canonical_url=data.canonical_url,
            no_index=data.no_index,
            created_by=created_by,
        )
        created = await self.repo.create(collection)

        if created_by:
            await self.notification_service.send_notification(
                user_id=created_by,
                title="Collection created",
                message=f'"{created.name}" was created.',
                notification_type=NotificationType.success,
                metadata={"collection_id": created.id, "slug": created.slug},
            )

        return created

    async def update_collection(self, collection_id: str, data) -> Collection:
        collection = await self.repo.get_by_id(collection_id)
        if not collection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")

        old_slug = collection.slug
        new_slug = collection.slug
        if data.slug is not None:
            new_slug = slugify(data.slug, fallback="collection")
            await self._ensure_unique_slug(new_slug, exclude_id=collection.id)
        elif data.name is not None:
            new_slug = slugify(data.name, fallback="collection")
            await self._ensure_unique_slug(new_slug, exclude_id=collection.id)

        if new_slug != old_slug:
            await self.slug_redirect_service.record("collection", old_slug, new_slug)
            collection.slug = new_slug

        changes = data.model_dump(exclude_unset=True, exclude={"slug", "rules", "collection_type"})
        for field, value in changes.items():
            setattr(collection, field, value)

        if data.collection_type is not None:
            collection.collection_type = CollectionType(data.collection_type.value)
        if data.rules is not None:
            collection.rules = [rule.model_dump() for rule in data.rules]

        return await self.repo.save(collection)

    async def delete_collection(self, collection_id: str) -> None:
        collection = await self.repo.get_by_id(collection_id)
        if not collection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")
        await self.repo.soft_delete(collection_id)

    async def bulk_delete(self, collection_ids: list[str]) -> int:
        return await self.repo.bulk_soft_delete(collection_ids)

    async def restore_collection(self, collection_id: str) -> Collection:
        collection = await self.repo.get_by_id_including_deleted(collection_id)
        if not collection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")
        if collection.deleted_at is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Collection is not deleted.")
        return await self.repo.restore(collection_id)

    async def get_collection(self, collection_id: str) -> Collection | None:
        return await self.repo.get_by_id(collection_id)

    async def list_collections(
        self,
        status_filter: CollectionStatus | None = None,
        is_featured: bool | None = None,
        q: str | None = None,
        sort_by: str = "sort_order",
        sort_order: str = "asc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Collection], int]:
        items = await self.repo.list(status_filter, is_featured, q, sort_by, sort_order, limit, offset)
        total = await self.repo.count(status_filter, is_featured, q)
        return items, total

    # ------------------------------------------------------------------
    # Manual membership
    # ------------------------------------------------------------------
    async def add_products(self, collection_id: str, product_ids: list[str]) -> None:
        collection = await self.repo.get_by_id(collection_id)
        if not collection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")
        if collection.collection_type != CollectionType.manual:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Products can only be added manually to manual collections.")
        for product_id in product_ids:
            if not await self.product_repo.get_by_id(product_id):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {product_id} not found.")
        await self.repo.add_products(collection_id, product_ids)

    async def remove_products(self, collection_id: str, product_ids: list[str]) -> None:
        collection = await self.repo.get_by_id(collection_id)
        if not collection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")
        await self.repo.remove_products(collection_id, product_ids)

    async def reorder_products(self, collection_id: str, product_ids: list[str]) -> None:
        await self.repo.reorder_products(collection_id, product_ids)

    async def get_products(self, collection_id: str) -> list[Product]:
        collection = await self.repo.get_by_id(collection_id)
        if not collection:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found.")

        if collection.collection_type == CollectionType.manual:
            return await self.repo.list_manual_products(collection_id)

        return await self._evaluate_dynamic_rules(collection.rules or [])

    async def _evaluate_dynamic_rules(self, rules: list[dict]) -> list[Product]:
        filters: dict = {}
        post_filters: list[dict] = []

        for rule in rules:
            field, operator, value = rule.get("field"), rule.get("operator", "eq"), rule.get("value")
            if operator == "eq" and field == "category_id":
                filters["category_id"] = value
            elif operator == "eq" and field == "brand_id":
                filters["brand_id"] = value
            elif operator == "eq" and field == "status":
                filters["status"] = ProductStatus(value)
            elif operator == "eq" and field == "is_featured":
                filters["is_featured"] = bool(value)
            elif operator == "eq" and field == "has_variants":
                filters["has_variants"] = bool(value)
            else:
                post_filters.append(rule)

        products = await self.product_repo.list(
            status=filters.get("status"),
            brand_id=filters.get("brand_id"),
            category_id=filters.get("category_id"),
            is_featured=filters.get("is_featured"),
            has_variants=filters.get("has_variants"),
            limit=DYNAMIC_RULE_LIMIT,
        )

        for rule in post_filters:
            if rule.get("field") == "tag" and rule.get("operator") == "contains":
                tag_value = rule.get("value")
                products = [p for p in products if p.tags and tag_value in p.tags]

        return products
