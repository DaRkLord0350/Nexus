from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipment import ShipmentStatus
from app.repositories.shipment_repository import ShipmentRepository
from app.repositories.shipping_provider_repository import ShippingProviderRepository

# Pragmatic cap for pulling shipments into Python for aggregation -- mirrors
# the same "fetch a bounded batch, aggregate in Python" pattern already used
# elsewhere in this codebase (e.g. ShippingRuleService.list_active_sorted)
# rather than adding per-dialect date-arithmetic SQL.
MAX_SHIPMENTS_FOR_ANALYTICS = 5000


class ShippingAnalyticsService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.shipment_repo = ShipmentRepository(session, organization_id, is_superuser)
        self.provider_repo = ShippingProviderRepository(session, organization_id, is_superuser)

    def _percent(self, part: int, whole: int) -> float:
        return round(part / whole * 100, 2) if whole else 0.0

    async def get_courier_performance(self, date_from: datetime | None = None, date_to: datetime | None = None) -> dict:
        shipments = await self.shipment_repo.list(limit=MAX_SHIPMENTS_FOR_ANALYTICS)
        if date_from:
            shipments = [s for s in shipments if s.created_at >= date_from]
        if date_to:
            shipments = [s for s in shipments if s.created_at <= date_to]

        providers = await self.provider_repo.list(limit=200)
        provider_map = {p.id: p for p in providers}

        grouped: dict[str, list] = {}
        for shipment in shipments:
            if not shipment.shipping_provider_id:
                continue
            grouped.setdefault(shipment.shipping_provider_id, []).append(shipment)

        provider_stats = []
        for provider_id, group in grouped.items():
            provider = provider_map.get(provider_id)
            total = len(group)
            delivered = [s for s in group if s.status == ShipmentStatus.delivered]
            failed = [s for s in group if s.status == ShipmentStatus.failed_delivery]
            cod = [s for s in group if s.is_cod]

            transit_days: list[float] = []
            sla_met = 0
            for shipment in delivered:
                if shipment.delivered_at and shipment.created_at:
                    days = (shipment.delivered_at - shipment.created_at).total_seconds() / 86400
                    transit_days.append(days)
                    if provider and provider.base_transit_days is not None and days <= provider.base_transit_days:
                        sla_met += 1

            total_cost = round(sum(s.shipping_cost for s in group), 2)
            provider_stats.append({
                "shipping_provider_id": provider_id,
                "provider_name": provider.name if provider else "Unknown provider",
                "total_shipments": total,
                "delivered_count": len(delivered),
                "delivered_rate": self._percent(len(delivered), total),
                "failed_delivery_count": len(failed),
                "failed_delivery_rate": self._percent(len(failed), total),
                "cod_count": len(cod),
                "cod_rate": self._percent(len(cod), total),
                "avg_transit_days": round(sum(transit_days) / len(transit_days), 2) if transit_days else None,
                "total_shipping_cost": total_cost,
                "avg_shipping_cost": round(total_cost / total, 2) if total else 0.0,
                "sla_met_count": sla_met,
                "sla_met_rate": self._percent(sla_met, len(delivered)) if delivered else None,
            })

        provider_stats.sort(key=lambda s: s["total_shipments"], reverse=True)

        total = len(shipments)
        delivered_all = [s for s in shipments if s.status == ShipmentStatus.delivered]
        failed_all = [s for s in shipments if s.status == ShipmentStatus.failed_delivery]
        cod_all = [s for s in shipments if s.is_cod]
        summary = {
            "total_shipments": total,
            "delivered_count": len(delivered_all),
            "delivered_rate": self._percent(len(delivered_all), total),
            "failed_delivery_count": len(failed_all),
            "failed_delivery_rate": self._percent(len(failed_all), total),
            "cod_count": len(cod_all),
            "cod_rate": self._percent(len(cod_all), total),
            "total_shipping_cost": round(sum(s.shipping_cost for s in shipments), 2),
        }

        return {"date_from": date_from, "date_to": date_to, "summary": summary, "providers": provider_stats}
