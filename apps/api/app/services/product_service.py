from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationType
from app.models.product import Product, ProductStatus
from app.repositories.brand_repository import BrandRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.product_type_repository import ProductTypeRepository
from app.repositories.tag_repository import TagRepository
from app.repositories.tax_class_repository import TaxClassRepository
from app.services.notification_service import NotificationService
from app.services.slug_redirect_service import SlugRedirectService
from app.services.tag_service import TagService
from app.utils.text import slugify


class ProductService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = ProductRepository(session, organization_id, is_superuser)
        self.brand_repo = BrandRepository(session, organization_id, is_superuser)
        self.category_repo = CategoryRepository(session, organization_id, is_superuser)
        self.tax_class_repo = TaxClassRepository(session, organization_id, is_superuser)
        self.product_type_repo = ProductTypeRepository(session, organization_id, is_superuser)
        self.tag_repo = TagRepository(session, organization_id, is_superuser)
        self.tag_service = TagService(session, organization_id, is_superuser)
        self.notification_service = NotificationService(session, organization_id, is_superuser)
        self.slug_redirect_service = SlugRedirectService(session, organization_id, is_superuser)

    async def _enrich(self, product: Product) -> Product:
        product.tags = await self.tag_repo.get_tags_for_product(product.id)
        return product

    async def _enrich_many(self, products: list[Product]) -> list[Product]:
        grouped = await self.tag_repo.get_tags_for_products([p.id for p in products])
        for product in products:
            product.tags = grouped.get(product.id, [])
        return products

    async def _set_tags_by_name(self, product_id: str, tag_names: list[str]) -> None:
        tags = await self.tag_service.get_or_create_by_names(tag_names)
        await self.tag_repo.set_product_tags(product_id, [tag.id for tag in tags])

    async def _ensure_unique_slug(self, slug: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_slug(slug)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A product with that slug already exists.")

    async def _ensure_unique_sku(self, sku: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_sku(sku)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A product with that SKU already exists.")

    async def _validate_references(
        self, brand_id: str | None, category_id: str | None, tax_class_id: str | None = None, product_type_id: str | None = None,
    ) -> None:
        if brand_id and not await self.brand_repo.get_by_id(brand_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found.")
        if category_id and not await self.category_repo.get_by_id(category_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
        if tax_class_id and not await self.tax_class_repo.get_by_id(tax_class_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tax class not found.")
        if product_type_id and not await self.product_type_repo.get_by_id(product_type_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product type not found.")

    async def create_product(self, data, created_by: str | None = None) -> Product:
        await self._validate_references(data.brand_id, data.category_id, data.tax_class_id, data.product_type_id)
        slug = slugify(data.slug or data.name, fallback="product")
        await self._ensure_unique_slug(slug)
        await self._ensure_unique_sku(data.sku)

        product = Product(
            name=data.name,
            slug=slug,
            sku=data.sku,
            barcode=data.barcode,
            brand_id=data.brand_id,
            category_id=data.category_id,
            tax_class_id=data.tax_class_id,
            product_type_id=data.product_type_id,
            description=data.description,
            short_description=data.short_description,
            status=ProductStatus(data.status.value),
            seo_title=data.seo_title,
            seo_description=data.seo_description,
            seo_keywords=data.seo_keywords,
            og_image_url=data.og_image_url,
            canonical_url=data.canonical_url,
            no_index=data.no_index,
            length=data.length,
            width=data.width,
            height=data.height,
            dimension_unit=data.dimension_unit,
            weight=data.weight,
            weight_unit=data.weight_unit,
            origin_country=data.origin_country,
            vendor=data.vendor,
            search_keywords=data.search_keywords,
            track_inventory=data.track_inventory,
            allow_backorders=data.allow_backorders,
            has_variants=data.has_variants,
            is_featured=data.is_featured,
            published_at=datetime.utcnow() if data.status == ProductStatus.published else None,
            created_by=created_by,
        )
        created = await self.repo.create(product)

        if data.tag_names:
            await self._set_tags_by_name(created.id, data.tag_names)

        return await self._enrich(created)

    async def update_product(self, product_id: str, data) -> Product:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

        await self._validate_references(data.brand_id, data.category_id, data.tax_class_id, data.product_type_id)

        old_slug = product.slug
        new_slug = product.slug
        if data.slug is not None:
            new_slug = slugify(data.slug, fallback="product")
            await self._ensure_unique_slug(new_slug, exclude_id=product.id)
        elif data.name is not None:
            new_slug = slugify(data.name, fallback="product")
            await self._ensure_unique_slug(new_slug, exclude_id=product.id)

        if new_slug != old_slug:
            await self.slug_redirect_service.record("product", old_slug, new_slug)
            product.slug = new_slug

        if data.sku is not None:
            await self._ensure_unique_sku(data.sku, exclude_id=product.id)

        was_published = product.status == ProductStatus.published
        changes = data.model_dump(exclude_unset=True, exclude={"slug", "tag_names"})
        for field, value in changes.items():
            if field == "status" and value is not None:
                value = ProductStatus(value.value if hasattr(value, "value") else value)
            setattr(product, field, value)

        if not was_published and product.status == ProductStatus.published:
            product.published_at = datetime.utcnow()
            await self._notify_published(product)

        saved = await self.repo.save(product)

        if data.tag_names is not None:
            await self._set_tags_by_name(product_id, data.tag_names)

        return await self._enrich(saved)

    async def publish_product(self, product_id: str, actor_id: str) -> Product:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        product.status = ProductStatus.published
        product.published_at = datetime.utcnow()
        saved = await self.repo.save(product)
        await self._notify_published(saved, actor_id)
        return await self._enrich(saved)

    async def archive_product(self, product_id: str) -> Product:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        product.status = ProductStatus.archived
        saved = await self.repo.save(product)
        return await self._enrich(saved)

    async def _notify_published(self, product: Product, actor_id: str | None = None) -> None:
        recipient_id = actor_id or product.created_by
        if not recipient_id:
            return
        await self.notification_service.send_notification(
            user_id=recipient_id,
            title="Product published",
            message=f'"{product.name}" is now live.',
            notification_type=NotificationType.success,
            metadata={"product_id": product.id, "slug": product.slug},
        )

    async def delete_product(self, product_id: str) -> None:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        await self.repo.soft_delete(product_id)

    async def bulk_delete(self, product_ids: list[str]) -> int:
        return await self.repo.bulk_soft_delete(product_ids)

    async def bulk_update_status(self, product_ids: list[str], new_status: ProductStatus) -> int:
        return await self.repo.bulk_update_status(product_ids, new_status)

    async def restore_product(self, product_id: str) -> Product:
        product = await self.repo.get_by_id_including_deleted(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        if product.deleted_at is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product is not deleted.")
        restored = await self.repo.restore(product_id)
        return await self._enrich(restored)

    async def get_product(self, product_id: str) -> Product | None:
        product = await self.repo.get_by_id(product_id)
        if not product:
            return None
        return await self._enrich(product)

    async def get_by_slug(self, slug: str) -> Product | None:
        return await self.repo.get_by_slug(slug)

    async def list_products(
        self,
        status_filter: ProductStatus | None = None,
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
    ) -> tuple[list[Product], int]:
        items = await self.repo.list(status_filter, brand_id, category_id, is_featured, has_variants, q, sort_by, sort_order, limit, offset, tag_id)
        items = await self._enrich_many(items)
        total = await self.repo.count(status_filter, brand_id, category_id, is_featured, has_variants, q, tag_id)
        return items, total
