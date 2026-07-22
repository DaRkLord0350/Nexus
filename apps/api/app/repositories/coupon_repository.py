from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete as sa_delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coupon import Coupon
from app.models.coupon_redemption import CouponRedemption
from app.models.coupon_restriction import CouponCategory, CouponCollection, CouponProduct
from app.repositories.base_repository import BaseRepository

SORTABLE_FIELDS = {
    "code": Coupon.code,
    "created_at": Coupon.created_at,
    "expires_at": Coupon.expires_at,
}


class CouponRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, coupon: Coupon) -> Coupon:
        self._add_tenant_on_create(coupon)
        self.session.add(coupon)
        await self.session.commit()
        await self.session.refresh(coupon)
        return coupon

    async def save(self, coupon: Coupon) -> Coupon:
        self.session.add(coupon)
        await self.session.commit()
        await self.session.refresh(coupon)
        return coupon

    async def get_by_id(self, coupon_id: str) -> Coupon | None:
        statement = select(Coupon).where(Coupon.id == coupon_id)
        statement = self._apply_tenant_filter(statement, Coupon)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Coupon | None:
        statement = select(Coupon).where(Coupon.code == code)
        statement = self._apply_tenant_filter(statement, Coupon)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(self, statement, is_active: bool | None = None, q: str | None = None):
        if is_active is not None:
            statement = statement.where(Coupon.is_active == is_active)
        if q:
            like = f"%{q}%"
            statement = statement.where(or_(Coupon.code.ilike(like), Coupon.name.ilike(like)))
        return statement

    async def list(
        self,
        is_active: bool | None = None,
        q: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Coupon]:
        column = SORTABLE_FIELDS.get(sort_by, Coupon.created_at)
        order_clause = column.desc() if sort_order == "desc" else column.asc()
        statement = select(Coupon).order_by(order_clause).limit(limit).offset(offset)
        statement = self._apply_filters(statement, is_active, q)
        statement = self._apply_tenant_filter(statement, Coupon)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count(self, is_active: bool | None = None, q: str | None = None) -> int:
        statement = select(func.count(Coupon.id))
        statement = self._apply_filters(statement, is_active, q)
        statement = self._apply_tenant_filter(statement, Coupon)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def list_expired_unnotified(self, at_time: datetime) -> list[Coupon]:
        statement = select(Coupon).where(
            Coupon.expires_at.is_not(None),
            Coupon.expires_at < at_time,
            Coupon.is_active.is_(True),
            Coupon.expired_notified_at.is_(None),
        )
        statement = self._apply_tenant_filter(statement, Coupon)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def soft_delete(self, coupon_id: str) -> None:
        statement = update(Coupon).where(Coupon.id == coupon_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Coupon)
        await self.session.execute(statement)
        await self.session.commit()

    async def bulk_soft_delete(self, coupon_ids: list[str]) -> int:
        if not coupon_ids:
            return 0
        statement = update(Coupon).where(Coupon.id.in_(coupon_ids)).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, Coupon)
        result = await self.session.execute(statement)
        await self.session.commit()
        return result.rowcount or 0

    async def increment_used_count(self, coupon_id: str) -> None:
        statement = update(Coupon).where(Coupon.id == coupon_id).values(used_count=Coupon.used_count + 1)
        statement = self._apply_tenant_filter(statement, Coupon)
        await self.session.execute(statement)
        await self.session.commit()

    # ------------------------------------------------------------------
    # Restrictions
    # ------------------------------------------------------------------
    async def set_product_restrictions(self, coupon_id: str, product_ids: list[str]) -> None:
        await self.session.execute(sa_delete(CouponProduct).where(CouponProduct.coupon_id == coupon_id))
        for product_id in product_ids:
            link = CouponProduct(coupon_id=coupon_id, product_id=product_id)
            self._add_tenant_on_create(link)
            self.session.add(link)
        await self.session.commit()

    async def set_category_restrictions(self, coupon_id: str, category_ids: list[str]) -> None:
        await self.session.execute(sa_delete(CouponCategory).where(CouponCategory.coupon_id == coupon_id))
        for category_id in category_ids:
            link = CouponCategory(coupon_id=coupon_id, category_id=category_id)
            self._add_tenant_on_create(link)
            self.session.add(link)
        await self.session.commit()

    async def set_collection_restrictions(self, coupon_id: str, collection_ids: list[str]) -> None:
        await self.session.execute(sa_delete(CouponCollection).where(CouponCollection.coupon_id == coupon_id))
        for collection_id in collection_ids:
            link = CouponCollection(coupon_id=coupon_id, collection_id=collection_id)
            self._add_tenant_on_create(link)
            self.session.add(link)
        await self.session.commit()

    async def get_restrictions(self, coupon_id: str) -> dict[str, list[str]]:
        product_ids = (await self.session.execute(select(CouponProduct.product_id).where(CouponProduct.coupon_id == coupon_id))).scalars().all()
        category_ids = (await self.session.execute(select(CouponCategory.category_id).where(CouponCategory.coupon_id == coupon_id))).scalars().all()
        collection_ids = (await self.session.execute(select(CouponCollection.collection_id).where(CouponCollection.coupon_id == coupon_id))).scalars().all()
        return {"product_ids": list(product_ids), "category_ids": list(category_ids), "collection_ids": list(collection_ids)}

    # ------------------------------------------------------------------
    # Redemptions
    # ------------------------------------------------------------------
    async def create_redemption(self, redemption: CouponRedemption) -> CouponRedemption:
        self._add_tenant_on_create(redemption)
        self.session.add(redemption)
        await self.session.commit()
        await self.session.refresh(redemption)
        return redemption

    async def count_redemptions_for_user(self, coupon_id: str, user_id: str) -> int:
        statement = select(func.count(CouponRedemption.id)).where(
            CouponRedemption.coupon_id == coupon_id, CouponRedemption.user_id == user_id
        )
        result = await self.session.execute(statement)
        return result.scalar_one()
