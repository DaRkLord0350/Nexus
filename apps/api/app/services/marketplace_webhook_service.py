import json
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace_order_link import MarketplaceOrderLinkStatus
from app.models.marketplace_webhook_event import MarketplaceWebhookEvent, MarketplaceWebhookStatus
from app.repositories.marketplace_connector_repository import MarketplaceConnectorRepository
from app.repositories.marketplace_product_link_repository import MarketplaceProductLinkRepository
from app.repositories.marketplace_webhook_event_repository import MarketplaceWebhookEventRepository
from app.services.marketplace_sync_service import MarketplaceSyncService

# Retry-with-backoff schedule (minutes), indexed by retry_count. No Celery
# beat/worker is configured in this codebase, so there is no automatic timer
# driving retries -- `retry_due_events()` is a manual "retry now" action
# (exposed as a staff endpoint / button) that processes whatever is
# currently due, standing in for a scheduled retry worker.
BACKOFF_MINUTES = [1, 5, 15, 60, 240]
MAX_RETRIES = len(BACKOFF_MINUTES)

ORDER_EVENT_TYPES = {"order.created", "order.updated"}
INVENTORY_EVENT_TYPES = {"inventory.updated"}


class MarketplaceWebhookService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.connector_repo = MarketplaceConnectorRepository(session, organization_id, is_superuser)
        self.event_repo = MarketplaceWebhookEventRepository(session, organization_id, is_superuser)
        self.link_repo = MarketplaceProductLinkRepository(session, organization_id, is_superuser)
        self.sync_service = MarketplaceSyncService(session, organization_id, is_superuser)

    async def _process_event(self, connector, event: MarketplaceWebhookEvent) -> MarketplaceWebhookEvent:
        payload = json.loads(event.payload)
        try:
            if event.event_type in ORDER_EVENT_TYPES:
                link = await self.sync_service.import_order_payload(connector, payload)
                if link.status != MarketplaceOrderLinkStatus.imported:
                    raise ValueError(link.last_error or "Order import failed.")
            elif event.event_type in INVENTORY_EVENT_TYPES:
                product_link = None
                for candidate in await self.link_repo.list(connector_id=connector.id, limit=200):
                    if candidate.external_id == payload.get("external_id"):
                        product_link = candidate
                        break
                if not product_link:
                    raise ValueError("No linked product found for that external_id.")
                product_link.last_synced_quantity = payload.get("quantity")
                product_link.last_synced_at = datetime.utcnow()
                await self.link_repo.save(product_link)
            # Unrecognized event types are accepted and marked processed
            # (best-effort ingestion) rather than rejected -- a real
            # integration would extend the two branches above per event.

            event.status = MarketplaceWebhookStatus.processed
            event.processed_at = datetime.utcnow()
            event.last_error = None
        except Exception as exc:  # noqa: BLE001 -- failures schedule a retry, they never crash the webhook endpoint
            event.status = MarketplaceWebhookStatus.failed
            event.last_error = str(exc)
            if event.retry_count < MAX_RETRIES:
                delay = BACKOFF_MINUTES[event.retry_count]
                event.next_retry_at = datetime.utcnow() + timedelta(minutes=delay)
            else:
                event.next_retry_at = None
            event.retry_count += 1

        return await self.event_repo.save(event)

    async def process_webhook(self, data, webhook_secret: str | None = None) -> MarketplaceWebhookEvent:
        connector = await self.connector_repo.get_by_code(data.connector_code)
        if not connector:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown marketplace connector code.")
        if connector.webhook_secret and connector.webhook_secret != webhook_secret:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook secret.")

        event = MarketplaceWebhookEvent(
            marketplace_connector_id=connector.id,
            event_type=data.event_type,
            payload=json.dumps(data.payload),
            received_at=datetime.utcnow(),
        )
        event = await self.event_repo.create(event)
        return await self._process_event(connector, event)

    async def retry_due_events(self, connector_id: str | None = None) -> list[MarketplaceWebhookEvent]:
        due = await self.event_repo.list_due_for_retry(limit=100)
        if connector_id:
            due = [e for e in due if e.marketplace_connector_id == connector_id]

        results = []
        for event in due:
            connector = await self.connector_repo.get_by_id(event.marketplace_connector_id)
            if not connector:
                continue
            results.append(await self._process_event(connector, event))
        return results

    async def list_events(self, connector_id: str | None = None, status_filter: str | None = None, limit: int = 50, offset: int = 0):
        items = await self.event_repo.list(connector_id, status_filter, limit, offset)
        total = await self.event_repo.count(connector_id, status_filter)
        return items, total
