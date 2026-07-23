from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipping_rate import ShippingRate
from app.repositories.base_repository import BaseRepository


class ShippingRateRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, rate: ShippingRate) -> ShippingRate:
        self._add_tenant_on_create(rate)
        self.session.add(rate)
        await self.session.commit()
        await self.session.refresh(rate)
        return rate

    async def save(self, rate: ShippingRate) -> ShippingRate:
        self.session.add(rate)
        await self.session.commit()
        await self.session.refresh(rate)
        return rate

    async def get_by_id(self, rate_id: str) -> ShippingRate | None:
        statement = select(ShippingRate).where(ShippingRate.id == rate_id)
        statement = self._apply_tenant_filter(statement, ShippingRate)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_provider(self, shipping_provider_id: str, limit: int = 100, offset: int = 0) -> list[ShippingRate]:
        statement = (
            select(ShippingRate).where(ShippingRate.shipping_provider_id == shipping_provider_id)
            .order_by(ShippingRate.created_at.desc()).limit(limit).offset(offset)
        )
        statement = self._apply_tenant_filter(statement, ShippingRate)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count_for_provider(self, shipping_provider_id: str) -> int:
        statement = select(func.count(ShippingRate.id)).where(ShippingRate.shipping_provider_id == shipping_provider_id)
        statement = self._apply_tenant_filter(statement, ShippingRate)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def list_matching(self, destination_country: str, destination_state: str | None, weight: float) -> list[ShippingRate]:
        statement = select(ShippingRate).where(
            ShippingRate.is_active.is_(True),
            or_(ShippingRate.destination_country.is_(None), ShippingRate.destination_country == destination_country),
        )
        statement = self._apply_tenant_filter(statement, ShippingRate)
        result = await self.session.execute(statement)
        candidates = result.scalars().all()

        matching = []
        for rate in candidates:
            if rate.destination_state and rate.destination_state != destination_state:
                continue
            if rate.min_weight is not None and weight < rate.min_weight:
                continue
            if rate.max_weight is not None and weight > rate.max_weight:
                continue
            matching.append(rate)
        return matching

    async def soft_delete(self, rate_id: str) -> None:
        statement = update(ShippingRate).where(ShippingRate.id == rate_id).values(deleted_at=datetime.utcnow())
        statement = self._apply_tenant_filter(statement, ShippingRate)
        await self.session.execute(statement)
        await self.session.commit()
