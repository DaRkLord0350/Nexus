from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationType
from app.models.product_price import ProductPrice
from app.repositories.product_price_repository import ProductPriceRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.variant_repository import VariantRepository
from app.services.notification_service import NotificationService


class PricingService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = ProductPriceRepository(session, organization_id, is_superuser)
        self.product_repo = ProductRepository(session, organization_id, is_superuser)
        self.variant_repo = VariantRepository(session, organization_id, is_superuser)
        self.notification_service = NotificationService(session, organization_id, is_superuser)

    async def _validate_references(self, product_id: str, variant_id: str | None) -> None:
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        if variant_id:
            variant = await self.variant_repo.get_by_id(variant_id)
            if not variant or variant.product_id != product_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found for this product.")

    async def _notify_price_changed(self, price: ProductPrice, actor_id: str | None) -> None:
        product = await self.product_repo.get_by_id(price.product_id)
        recipient_id = actor_id or (product.created_by if product else None)
        if not recipient_id or not product:
            return
        await self.notification_service.send_notification(
            user_id=recipient_id,
            title="Price changed",
            message=f'Pricing for "{product.name}" was updated.',
            notification_type=NotificationType.info,
            metadata={"product_id": price.product_id, "variant_id": price.variant_id, "price_id": price.id},
        )

    async def create_price(self, data, created_by: str | None = None) -> ProductPrice:
        await self._validate_references(data.product_id, data.variant_id)

        price = ProductPrice(
            product_id=data.product_id,
            variant_id=data.variant_id,
            currency=data.currency.upper(),
            mrp=data.mrp,
            selling_price=data.selling_price,
            cost_price=data.cost_price,
            compare_price=data.compare_price,
            min_price=data.min_price,
            max_price=data.max_price,
            customer_group=data.customer_group,
            region=data.region,
            effective_from=data.effective_from,
            effective_to=data.effective_to,
            is_active=data.is_active,
            created_by=created_by,
        )
        created = await self.repo.create(price)
        await self._notify_price_changed(created, created_by)
        return created

    async def update_price(self, price_id: str, data, actor_id: str | None = None) -> ProductPrice:
        price = await self.repo.get_by_id(price_id)
        if not price:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price not found.")

        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            if field == "currency" and value is not None:
                value = value.upper()
            setattr(price, field, value)

        saved = await self.repo.save(price)
        await self._notify_price_changed(saved, actor_id)
        return saved

    async def delete_price(self, price_id: str) -> None:
        price = await self.repo.get_by_id(price_id)
        if not price:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price not found.")
        await self.repo.soft_delete(price_id)

    async def bulk_delete(self, price_ids: list[str]) -> int:
        return await self.repo.bulk_soft_delete(price_ids)

    async def get_price(self, price_id: str) -> ProductPrice | None:
        return await self.repo.get_by_id(price_id)

    async def list_prices(
        self,
        product_id: str,
        variant_id: str | None = "__unset__",
        currency: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ProductPrice], int]:
        items = await self.repo.list_for_product(product_id, variant_id, currency, limit, offset)
        total = await self.repo.count_for_product(product_id, variant_id, currency)
        return items, total

    async def resolve_price(
        self,
        product_id: str,
        currency: str,
        variant_id: str | None = None,
        customer_group: str | None = None,
        region: str | None = None,
        at_time: datetime | None = None,
    ) -> ProductPrice | None:
        """Picks the most specific active price row matching the given scope.

        Specificity score rewards an exact variant match, an exact region
        match, and an exact customer-group match; a row scoped to "any" for a
        dimension (null) always matches but scores lower than an exact match.
        """
        candidates = await self.repo.list_candidates(product_id, currency.upper(), at_time or datetime.utcnow())

        best: ProductPrice | None = None
        best_score = -1
        for candidate in candidates:
            if candidate.variant_id and candidate.variant_id != variant_id:
                continue
            if candidate.region and candidate.region != region:
                continue
            if candidate.customer_group and candidate.customer_group != customer_group:
                continue

            score = (
                (2 if candidate.variant_id else 0)
                + (1 if candidate.region else 0)
                + (1 if candidate.customer_group else 0)
            )
            if score > best_score:
                best_score = score
                best = candidate

        return best
