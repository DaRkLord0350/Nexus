from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace_order_link import MarketplaceOrderLinkStatus
from app.models.marketplace_product_link import MarketplaceLinkStatus
from app.models.marketplace_sync_log import MarketplaceSyncStatus
from app.models.marketplace_webhook_event import MarketplaceWebhookStatus
from app.repositories.marketplace_connector_repository import MarketplaceConnectorRepository
from app.repositories.marketplace_order_link_repository import MarketplaceOrderLinkRepository
from app.repositories.marketplace_product_link_repository import MarketplaceProductLinkRepository
from app.repositories.marketplace_sync_log_repository import MarketplaceSyncLogRepository
from app.repositories.marketplace_webhook_event_repository import MarketplaceWebhookEventRepository
from app.repositories.order_repository import OrderRepository

# Pragmatic cap for pulling rows into Python for aggregation -- mirrors the
# same "fetch a bounded batch, aggregate in Python" pattern used by
# ShippingAnalyticsService rather than adding per-dialect date-arithmetic SQL.
MAX_ROWS_FOR_ANALYTICS = 5000


class MarketplaceAnalyticsService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.connector_repo = MarketplaceConnectorRepository(session, organization_id, is_superuser)
        self.log_repo = MarketplaceSyncLogRepository(session, organization_id, is_superuser)
        self.product_link_repo = MarketplaceProductLinkRepository(session, organization_id, is_superuser)
        self.order_link_repo = MarketplaceOrderLinkRepository(session, organization_id, is_superuser)
        self.webhook_repo = MarketplaceWebhookEventRepository(session, organization_id, is_superuser)
        self.order_repo = OrderRepository(session, organization_id, is_superuser)

    def _percent(self, part: int, whole: int) -> float:
        return round(part / whole * 100, 2) if whole else 0.0

    async def get_dashboard(self, date_from: datetime | None = None, date_to: datetime | None = None) -> dict:
        connectors = await self.connector_repo.list(limit=200)
        logs = await self.log_repo.list(limit=MAX_ROWS_FOR_ANALYTICS)
        if date_from:
            logs = [l for l in logs if l.started_at >= date_from]
        if date_to:
            logs = [l for l in logs if l.started_at <= date_to]

        product_links = await self.product_link_repo.list(limit=MAX_ROWS_FOR_ANALYTICS)
        order_links = await self.order_link_repo.list(limit=MAX_ROWS_FOR_ANALYTICS)

        order_ids = [link.order_id for link in order_links if link.status == MarketplaceOrderLinkStatus.imported and link.order_id]
        revenue_by_order_id: dict[str, float] = {}
        for order_id in order_ids:
            order = await self.order_repo.get_by_id(order_id)
            if order:
                revenue_by_order_id[order_id] = order.total

        connector_stats = []
        for connector in connectors:
            connector_logs = [l for l in logs if l.marketplace_connector_id == connector.id]
            total_syncs = len(connector_logs)
            successful = len([l for l in connector_logs if l.status == MarketplaceSyncStatus.success])
            failed = len([l for l in connector_logs if l.status == MarketplaceSyncStatus.failed])

            durations = [
                (l.completed_at - l.started_at).total_seconds()
                for l in connector_logs if l.completed_at
            ]

            connector_order_links = [link for link in order_links if link.marketplace_connector_id == connector.id]
            imported_orders = [link for link in connector_order_links if link.status == MarketplaceOrderLinkStatus.imported]
            failed_orders = [link for link in connector_order_links if link.status == MarketplaceOrderLinkStatus.failed]
            revenue = round(sum(revenue_by_order_id.get(link.order_id, 0) for link in imported_orders), 2)

            connector_products = [link for link in product_links if link.marketplace_connector_id == connector.id]
            linked = len([link for link in connector_products if link.sync_status == MarketplaceLinkStatus.synced])
            product_failed = len([link for link in connector_products if link.sync_status == MarketplaceLinkStatus.failed])

            connector_stats.append({
                "marketplace_connector_id": connector.id,
                "connector_name": connector.name,
                "connector_type": connector.connector_type,
                "total_syncs": total_syncs,
                "successful_syncs": successful,
                "sync_success_rate": self._percent(successful, total_syncs),
                "failed_syncs": failed,
                "orders_imported": len(imported_orders),
                "orders_failed": len(failed_orders),
                "revenue_imported": revenue,
                "products_linked": linked,
                "products_failed": product_failed,
                "avg_sync_duration_seconds": round(sum(durations) / len(durations), 2) if durations else None,
            })

        connector_stats.sort(key=lambda s: s["total_syncs"], reverse=True)

        total_syncs = len(logs)
        successful_all = len([l for l in logs if l.status == MarketplaceSyncStatus.success])
        total_orders_imported = len([link for link in order_links if link.status == MarketplaceOrderLinkStatus.imported])
        total_revenue = round(sum(revenue_by_order_id.values()), 2)
        pending_retries = await self.webhook_repo.count(status_filter=MarketplaceWebhookStatus.failed.value)

        summary = {
            "total_syncs": total_syncs,
            "sync_success_rate": self._percent(successful_all, total_syncs),
            "total_orders_imported": total_orders_imported,
            "total_revenue_imported": total_revenue,
            "pending_webhook_retries": pending_retries,
        }

        return {"date_from": date_from, "date_to": date_to, "summary": summary, "connectors": connector_stats}
