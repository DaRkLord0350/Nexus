from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipping_rate import ShippingRate
from app.repositories.shipping_provider_repository import ShippingProviderRepository
from app.repositories.shipping_rate_repository import ShippingRateRepository

# Weights for the recommendation heuristic. This is a simple weighted-score
# ranking, not a trained model -- described as "AI recommendation" in the
# product brief, but there's no ML infra in this codebase to back a real one.
COST_WEIGHT = 0.4
SPEED_WEIGHT = 0.35
RATING_WEIGHT = 0.25
DEFAULT_RATING = 3.0


class ShippingRateService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = ShippingRateRepository(session, organization_id, is_superuser)
        self.provider_repo = ShippingProviderRepository(session, organization_id, is_superuser)

    async def create_rate(self, data, created_by: str | None = None) -> ShippingRate:
        provider = await self.provider_repo.get_by_id(data.shipping_provider_id)
        if not provider:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipping provider not found.")

        rate = ShippingRate(
            shipping_provider_id=data.shipping_provider_id,
            name=data.name,
            origin_country=data.origin_country,
            destination_country=data.destination_country,
            destination_state=data.destination_state,
            min_weight=data.min_weight,
            max_weight=data.max_weight,
            base_price=data.base_price,
            price_per_kg=data.price_per_kg,
            cod_fee=data.cod_fee,
            insurance_fee=data.insurance_fee,
            transit_days_min=data.transit_days_min,
            transit_days_max=data.transit_days_max,
            delivery_rating=data.delivery_rating,
            is_active=data.is_active,
        )
        return await self.repo.create(rate)

    async def _get_or_404(self, rate_id: str) -> ShippingRate:
        rate = await self.repo.get_by_id(rate_id)
        if not rate:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipping rate not found.")
        return rate

    async def get_rate(self, rate_id: str) -> ShippingRate | None:
        return await self.repo.get_by_id(rate_id)

    async def update_rate(self, rate_id: str, data) -> ShippingRate:
        rate = await self._get_or_404(rate_id)
        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(rate, field, value)
        return await self.repo.save(rate)

    async def delete_rate(self, rate_id: str) -> None:
        await self._get_or_404(rate_id)
        await self.repo.soft_delete(rate_id)

    async def list_rates_for_provider(self, shipping_provider_id: str, limit: int = 100, offset: int = 0) -> tuple[list[ShippingRate], int]:
        items = await self.repo.list_for_provider(shipping_provider_id, limit, offset)
        total = await self.repo.count_for_provider(shipping_provider_id)
        return items, total

    def _compute_cost(self, rate: ShippingRate, weight: float, is_cod: bool, needs_insurance: bool) -> float:
        cost = rate.base_price
        if rate.price_per_kg:
            extra_weight = max(0.0, weight - (rate.min_weight or 0))
            cost += extra_weight * rate.price_per_kg
        if is_cod and rate.cod_fee:
            cost += rate.cod_fee
        if needs_insurance and rate.insurance_fee:
            cost += rate.insurance_fee
        return round(cost, 2)

    async def compare_rates(self, data) -> list[dict]:
        matching_rates = await self.repo.list_matching(data.destination_country, data.destination_state, data.weight)
        best_rate_by_provider: dict[str, ShippingRate] = {}
        for rate in matching_rates:
            existing = best_rate_by_provider.get(rate.shipping_provider_id)
            candidate_cost = self._compute_cost(rate, data.weight, data.is_cod, data.needs_insurance)
            if not existing or candidate_cost < self._compute_cost(existing, data.weight, data.is_cod, data.needs_insurance):
                best_rate_by_provider[rate.shipping_provider_id] = rate

        providers = await self.provider_repo.list(is_active=True, limit=200)
        quotes = []
        for provider in providers:
            if data.is_cod and not provider.supports_cod:
                continue

            rate = best_rate_by_provider.get(provider.id)
            if rate:
                cost = self._compute_cost(rate, data.weight, data.is_cod, data.needs_insurance)
                transit_min, transit_max = rate.transit_days_min, rate.transit_days_max
                delivery_rating = rate.delivery_rating
                rate_id = rate.id
            elif provider.base_rate is not None:
                cost = provider.base_rate + (provider.base_rate * 0.1 if data.is_cod else 0)
                transit_min = transit_max = provider.base_transit_days
                delivery_rating = None
                rate_id = None
            else:
                continue

            quotes.append({
                "shipping_provider_id": provider.id,
                "provider_name": provider.name,
                "rate_id": rate_id,
                "cost": cost,
                "transit_days_min": transit_min,
                "transit_days_max": transit_max,
                "supports_cod": provider.supports_cod,
                "supports_insurance": provider.supports_insurance,
                "delivery_rating": delivery_rating,
                "recommended": False,
                "score": 0.0,
            })

        if not quotes:
            return quotes

        costs = [q["cost"] for q in quotes]
        transit_days = [q["transit_days_max"] or 999 for q in quotes]
        min_cost, max_cost = min(costs), max(costs)
        min_transit, max_transit = min(transit_days), max(transit_days)

        for quote in quotes:
            cost_score = 1.0 if max_cost == min_cost else 1 - (quote["cost"] - min_cost) / (max_cost - min_cost)
            transit = quote["transit_days_max"] or 999
            speed_score = 1.0 if max_transit == min_transit else 1 - (transit - min_transit) / (max_transit - min_transit)
            rating_score = (quote["delivery_rating"] or DEFAULT_RATING) / 5.0
            quote["score"] = round(COST_WEIGHT * cost_score + SPEED_WEIGHT * speed_score + RATING_WEIGHT * rating_score, 4)

        quotes.sort(key=lambda q: q["score"], reverse=True)
        if quotes:
            quotes[0]["recommended"] = True

        return quotes
