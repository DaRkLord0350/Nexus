from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coupon import Coupon, CouponDiscountType
from app.models.coupon_redemption import CouponRedemption
from app.models.notification import NotificationType
from app.repositories.coupon_repository import CouponRepository
from app.services.notification_service import NotificationService


class CouponService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = CouponRepository(session, organization_id, is_superuser)
        self.notification_service = NotificationService(session, organization_id, is_superuser)

    async def _ensure_unique_code(self, code: str, exclude_id: str | None = None) -> None:
        existing = await self.repo.get_by_code(code)
        if existing and existing.id != exclude_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A coupon with that code already exists.")

    async def _enrich(self, coupon: Coupon) -> Coupon:
        restrictions = await self.repo.get_restrictions(coupon.id)
        coupon.product_ids = restrictions["product_ids"]
        coupon.category_ids = restrictions["category_ids"]
        coupon.collection_ids = restrictions["collection_ids"]
        return coupon

    async def create_coupon(self, data, created_by: str | None = None) -> Coupon:
        code = data.code.strip().upper()
        await self._ensure_unique_code(code)

        coupon = Coupon(
            code=code,
            name=data.name,
            description=data.description,
            discount_type=CouponDiscountType(data.discount_type.value),
            discount_value=data.discount_value,
            buy_quantity=data.buy_quantity,
            get_quantity=data.get_quantity,
            get_discount_percentage=data.get_discount_percentage,
            min_order_amount=data.min_order_amount,
            max_discount_amount=data.max_discount_amount,
            usage_limit=data.usage_limit,
            usage_limit_per_customer=data.usage_limit_per_customer,
            starts_at=data.starts_at,
            expires_at=data.expires_at,
            is_active=data.is_active,
            created_by=created_by,
        )
        created = await self.repo.create(coupon)

        if data.product_ids:
            await self.repo.set_product_restrictions(created.id, data.product_ids)
        if data.category_ids:
            await self.repo.set_category_restrictions(created.id, data.category_ids)
        if data.collection_ids:
            await self.repo.set_collection_restrictions(created.id, data.collection_ids)

        return await self._enrich(created)

    async def update_coupon(self, coupon_id: str, data) -> Coupon:
        coupon = await self.repo.get_by_id(coupon_id)
        if not coupon:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found.")

        if data.code is not None:
            new_code = data.code.strip().upper()
            await self._ensure_unique_code(new_code, exclude_id=coupon.id)
            coupon.code = new_code

        changes = data.model_dump(exclude_unset=True, exclude={"code", "product_ids", "category_ids", "collection_ids"})
        for field, value in changes.items():
            if field == "discount_type" and value is not None:
                value = CouponDiscountType(value.value if hasattr(value, "value") else value)
            setattr(coupon, field, value)

        saved = await self.repo.save(coupon)

        if data.product_ids is not None:
            await self.repo.set_product_restrictions(coupon_id, data.product_ids)
        if data.category_ids is not None:
            await self.repo.set_category_restrictions(coupon_id, data.category_ids)
        if data.collection_ids is not None:
            await self.repo.set_collection_restrictions(coupon_id, data.collection_ids)

        return await self._enrich(saved)

    async def delete_coupon(self, coupon_id: str) -> None:
        coupon = await self.repo.get_by_id(coupon_id)
        if not coupon:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found.")
        await self.repo.soft_delete(coupon_id)

    async def bulk_delete(self, coupon_ids: list[str]) -> int:
        return await self.repo.bulk_soft_delete(coupon_ids)

    async def get_coupon(self, coupon_id: str) -> Coupon | None:
        coupon = await self.repo.get_by_id(coupon_id)
        if not coupon:
            return None
        return await self._enrich(coupon)

    async def list_coupons(
        self,
        is_active: bool | None = None,
        q: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Coupon], int]:
        items = await self.repo.list(is_active, q, sort_by, sort_order, limit, offset)
        for item in items:
            await self._enrich(item)
        total = await self.repo.count(is_active, q)
        return items, total

    # ------------------------------------------------------------------
    # Expiration
    # ------------------------------------------------------------------
    async def notify_expired_coupons(self) -> int:
        """Fires a one-time 'Coupon Expired' notification for coupons that have
        passed their expires_at and haven't been notified yet, and deactivates
        them. Invoked reactively from list/get rather than a background
        scheduler, since no Celery beat schedule exists in this codebase yet."""
        expired = await self.repo.list_expired_unnotified(datetime.utcnow())
        for coupon in expired:
            coupon.is_active = False
            coupon.expired_notified_at = datetime.utcnow()
            await self.repo.save(coupon)
            if coupon.created_by:
                await self.notification_service.send_notification(
                    user_id=coupon.created_by,
                    title="Coupon expired",
                    message=f'Coupon "{coupon.code}" has expired and was deactivated.',
                    notification_type=NotificationType.warning,
                    metadata={"coupon_id": coupon.id, "code": coupon.code},
                )
        return len(expired)

    # ------------------------------------------------------------------
    # Validation & discount calculation
    # ------------------------------------------------------------------
    async def validate_coupon(
        self,
        code: str,
        order_amount: float,
        product_ids: list[str] | None = None,
        category_ids: list[str] | None = None,
        collection_ids: list[str] | None = None,
        quantity: int = 1,
        unit_price: float = 0,
        customer_id: str | None = None,
    ) -> dict:
        await self.notify_expired_coupons()

        coupon = await self.repo.get_by_code(code.strip().upper())
        if not coupon:
            return {"valid": False, "reason": "Coupon not found.", "discount_amount": 0, "free_shipping": False, "coupon_id": None}

        now = datetime.utcnow()
        if not coupon.is_active:
            return {"valid": False, "reason": "Coupon is inactive.", "discount_amount": 0, "free_shipping": False, "coupon_id": coupon.id}
        if coupon.starts_at and now < coupon.starts_at:
            return {"valid": False, "reason": "Coupon is not yet valid.", "discount_amount": 0, "free_shipping": False, "coupon_id": coupon.id}
        if coupon.expires_at and now > coupon.expires_at:
            return {"valid": False, "reason": "Coupon has expired.", "discount_amount": 0, "free_shipping": False, "coupon_id": coupon.id}
        if coupon.min_order_amount and order_amount < coupon.min_order_amount:
            return {"valid": False, "reason": f"Order must be at least {coupon.min_order_amount}.", "discount_amount": 0, "free_shipping": False, "coupon_id": coupon.id}
        if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
            return {"valid": False, "reason": "Coupon usage limit reached.", "discount_amount": 0, "free_shipping": False, "coupon_id": coupon.id}
        if customer_id and coupon.usage_limit_per_customer is not None:
            used_by_customer = await self.repo.count_redemptions_for_user(coupon.id, customer_id)
            if used_by_customer >= coupon.usage_limit_per_customer:
                return {"valid": False, "reason": "You have already used this coupon.", "discount_amount": 0, "free_shipping": False, "coupon_id": coupon.id}

        restrictions = await self.repo.get_restrictions(coupon.id)
        if restrictions["product_ids"] or restrictions["category_ids"] or restrictions["collection_ids"]:
            matches = (
                any(pid in restrictions["product_ids"] for pid in (product_ids or []))
                or any(cid in restrictions["category_ids"] for cid in (category_ids or []))
                or any(coid in restrictions["collection_ids"] for coid in (collection_ids or []))
            )
            if not matches:
                return {"valid": False, "reason": "Coupon does not apply to these items.", "discount_amount": 0, "free_shipping": False, "coupon_id": coupon.id}

        discount_amount, free_shipping = self._calculate_discount(coupon, order_amount, quantity, unit_price)
        return {"valid": True, "reason": None, "discount_amount": discount_amount, "free_shipping": free_shipping, "coupon_id": coupon.id}

    def _calculate_discount(self, coupon: Coupon, order_amount: float, quantity: int, unit_price: float) -> tuple[float, bool]:
        if coupon.discount_type == CouponDiscountType.percentage:
            discount = order_amount * ((coupon.discount_value or 0) / 100)
            if coupon.max_discount_amount is not None:
                discount = min(discount, coupon.max_discount_amount)
            return round(min(discount, order_amount), 2), False

        if coupon.discount_type == CouponDiscountType.fixed_amount:
            discount = min(coupon.discount_value or 0, order_amount)
            return round(discount, 2), False

        if coupon.discount_type == CouponDiscountType.free_shipping:
            return 0.0, True

        if coupon.discount_type == CouponDiscountType.buy_x_get_y:
            if not coupon.buy_quantity or not coupon.get_quantity or unit_price <= 0:
                return 0.0, False
            bundle_size = coupon.buy_quantity + coupon.get_quantity
            bundles = quantity // bundle_size
            free_units = bundles * coupon.get_quantity
            discount = free_units * unit_price * ((coupon.get_discount_percentage or 100) / 100)
            return round(min(discount, order_amount), 2), False

        return 0.0, False

    async def redeem_coupon(self, coupon_id: str, customer_id: str | None = None, order_id: str | None = None) -> None:
        coupon = await self.repo.get_by_id(coupon_id)
        if not coupon:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found.")
        await self.repo.increment_used_count(coupon_id)
        redemption = CouponRedemption(coupon_id=coupon_id, user_id=customer_id, order_id=order_id)
        await self.repo.create_redemption(redemption)
