from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace_order_link import MarketplaceOrderLink, MarketplaceOrderLinkStatus
from app.models.marketplace_product_link import MarketplaceProductLink, MarketplaceLinkStatus
from app.models.marketplace_sync_log import MarketplaceSyncLog, MarketplaceSyncStatus, MarketplaceSyncType
from app.repositories.customer_repository import CustomerRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.marketplace_connector_repository import MarketplaceConnectorRepository
from app.repositories.marketplace_order_link_repository import MarketplaceOrderLinkRepository
from app.repositories.marketplace_product_link_repository import MarketplaceProductLinkRepository
from app.repositories.marketplace_sync_log_repository import MarketplaceSyncLogRepository
from app.repositories.product_price_repository import ProductPriceRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.order import OrderAddressInput, OrderCreateRequest, OrderLineItemInput
from app.services.marketplace_adapters import get_adapter
from app.services.order_service import OrderService

MAX_PRODUCTS_PER_SYNC = 200
DEFAULT_CURRENCY = "USD"


class MarketplaceSyncService:
    """Product/order/inventory/price sync engine. Request-triggered ("sync
    now") rather than running on a real schedule -- no Celery beat/worker is
    configured in this codebase (see MarketplaceWebhookEvent's module
    docstring). Each call writes a MarketplaceSyncLog row for observability
    and updates the connector's last_sync_at/last_sync_status."""

    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.connector_repo = MarketplaceConnectorRepository(session, organization_id, is_superuser)
        self.link_repo = MarketplaceProductLinkRepository(session, organization_id, is_superuser)
        self.order_link_repo = MarketplaceOrderLinkRepository(session, organization_id, is_superuser)
        self.log_repo = MarketplaceSyncLogRepository(session, organization_id, is_superuser)
        self.product_repo = ProductRepository(session, organization_id, is_superuser)
        self.price_repo = ProductPriceRepository(session, organization_id, is_superuser)
        self.inventory_repo = InventoryRepository(session, organization_id, is_superuser)
        self.customer_repo = CustomerRepository(session, organization_id, is_superuser)
        self.order_service = OrderService(session, organization_id, is_superuser)

    async def _get_connector_or_404(self, connector_id: str):
        connector = await self.connector_repo.get_by_id(connector_id)
        if not connector:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marketplace connector not found.")
        return connector

    async def _finish_log(self, log: MarketplaceSyncLog, connector) -> MarketplaceSyncLog:
        log.status = (
            MarketplaceSyncStatus.success if log.items_failed == 0
            else MarketplaceSyncStatus.partial if log.items_succeeded > 0
            else MarketplaceSyncStatus.failed
        )
        log.completed_at = datetime.utcnow()
        log = await self.log_repo.save(log)

        connector.last_sync_at = log.completed_at
        connector.last_sync_status = log.status.value
        await self.connector_repo.save(connector)
        return log

    async def sync_products(self, connector_id: str, product_ids: list[str] | None = None, triggered_by: str = "manual") -> MarketplaceSyncLog:
        connector = await self._get_connector_or_404(connector_id)
        adapter = get_adapter(connector.connector_type)

        if product_ids:
            products = [p for p in [await self.product_repo.get_by_id(pid) for pid in product_ids] if p]
        else:
            products = await self.product_repo.list(limit=MAX_PRODUCTS_PER_SYNC)

        log = MarketplaceSyncLog(marketplace_connector_id=connector.id, sync_type=MarketplaceSyncType.product, status=MarketplaceSyncStatus.success, triggered_by=triggered_by)
        log = await self.log_repo.create(log)

        for product in products:
            log.items_processed += 1
            link = None
            try:
                link = await self.link_repo.get_by_connector_and_product(connector.id, product.id)
                if not link:
                    link = MarketplaceProductLink(marketplace_connector_id=connector.id, product_id=product.id)

                result = await adapter.push_product(product)
                link.external_id = result["external_id"]
                link.external_url = result["external_url"]
                link.external_sku = link.external_sku or product.sku
                link.sync_status = MarketplaceLinkStatus.synced
                link.last_synced_at = datetime.utcnow()
                link.last_error = None

                if link.id:
                    await self.link_repo.save(link)
                else:
                    await self.link_repo.create(link)
                log.items_succeeded += 1
            except Exception as exc:  # noqa: BLE001 -- best-effort per-item sync, one bad product shouldn't abort the batch
                log.items_failed += 1
                if link is not None:
                    link.sync_status = MarketplaceLinkStatus.failed
                    link.last_error = str(exc)
                    if link.id:
                        await self.link_repo.save(link)
                    else:
                        await self.link_repo.create(link)

        return await self._finish_log(log, connector)

    async def sync_inventory(self, connector_id: str, product_ids: list[str] | None = None, triggered_by: str = "manual") -> MarketplaceSyncLog:
        connector = await self._get_connector_or_404(connector_id)
        adapter = get_adapter(connector.connector_type)

        links = await self.link_repo.list(connector_id=connector.id, limit=MAX_PRODUCTS_PER_SYNC)
        if product_ids:
            links = [link for link in links if link.product_id in product_ids]

        log = MarketplaceSyncLog(marketplace_connector_id=connector.id, sync_type=MarketplaceSyncType.inventory, status=MarketplaceSyncStatus.success, triggered_by=triggered_by)
        log = await self.log_repo.create(log)

        for link in links:
            log.items_processed += 1
            try:
                if not link.external_id:
                    raise ValueError("Product is not yet listed on this marketplace.")
                stock_rows = await self.inventory_repo.list(product_id=link.product_id, limit=500)
                quantity = sum(row.quantity_available for row in stock_rows)
                await adapter.push_inventory(link.external_id, quantity)

                link.last_synced_quantity = quantity
                link.last_synced_at = datetime.utcnow()
                link.last_error = None
                await self.link_repo.save(link)
                log.items_succeeded += 1
            except Exception as exc:  # noqa: BLE001
                log.items_failed += 1
                link.last_error = str(exc)
                await self.link_repo.save(link)

        return await self._finish_log(log, connector)

    async def sync_prices(self, connector_id: str, product_ids: list[str] | None = None, triggered_by: str = "manual") -> MarketplaceSyncLog:
        connector = await self._get_connector_or_404(connector_id)
        adapter = get_adapter(connector.connector_type)

        links = await self.link_repo.list(connector_id=connector.id, limit=MAX_PRODUCTS_PER_SYNC)
        if product_ids:
            links = [link for link in links if link.product_id in product_ids]

        log = MarketplaceSyncLog(marketplace_connector_id=connector.id, sync_type=MarketplaceSyncType.price, status=MarketplaceSyncStatus.success, triggered_by=triggered_by)
        log = await self.log_repo.create(log)

        for link in links:
            log.items_processed += 1
            try:
                if not link.external_id:
                    raise ValueError("Product is not yet listed on this marketplace.")
                candidates = await self.price_repo.list_candidates(link.product_id, DEFAULT_CURRENCY, datetime.utcnow())
                if not candidates:
                    raise ValueError(f"No active {DEFAULT_CURRENCY} price found for this product.")
                price = candidates[0].selling_price
                await adapter.push_price(link.external_id, price)

                link.last_synced_price = price
                link.last_synced_at = datetime.utcnow()
                link.last_error = None
                await self.link_repo.save(link)
                log.items_succeeded += 1
            except Exception as exc:  # noqa: BLE001
                log.items_failed += 1
                link.last_error = str(exc)
                await self.link_repo.save(link)

        return await self._finish_log(log, connector)

    async def import_order_payload(self, connector, payload: dict) -> MarketplaceOrderLink:
        """Shared by sync_orders (polling) and the webhook receiver
        (order.created/order.updated events) -- see marketplace_adapters.py
        module docstring for why polling yields nothing in this mock."""
        import json as _json

        external_order_id = str(payload["external_order_id"])
        existing = await self.order_link_repo.get_by_connector_and_external_id(connector.id, external_order_id)
        if existing:
            return existing

        link = MarketplaceOrderLink(
            marketplace_connector_id=connector.id,
            external_order_id=external_order_id,
            external_order_number=payload.get("external_order_number"),
            raw_payload=_json.dumps(payload),
            status=MarketplaceOrderLinkStatus.failed,
        )

        try:
            items_payload = payload.get("items") or []
            order_items: list[OrderLineItemInput] = []
            for item in items_payload:
                link_match = None
                if item.get("external_id"):
                    for candidate in await self.link_repo.list(connector_id=connector.id, limit=MAX_PRODUCTS_PER_SYNC):
                        if candidate.external_id == item["external_id"]:
                            link_match = candidate
                            break
                if not link_match and item.get("external_sku"):
                    for candidate in await self.link_repo.list(connector_id=connector.id, limit=MAX_PRODUCTS_PER_SYNC):
                        if candidate.external_sku == item["external_sku"]:
                            link_match = candidate
                            break
                if not link_match:
                    continue
                order_items.append(OrderLineItemInput(
                    product_id=link_match.product_id,
                    quantity=int(item.get("quantity", 1)),
                    unit_price=item.get("unit_price"),
                ))

            if not order_items:
                raise ValueError("No matching linked products found for this order's line items.")

            email = payload.get("customer_email")
            customer = await self.customer_repo.get_by_email(email) if email else None
            if not customer:
                from app.models.customer import Customer
                customer = Customer(
                    email=email or f"{external_order_id}@{connector.connector_type}.marketplace",
                    first_name=payload.get("customer_first_name") or "Marketplace",
                    last_name=payload.get("customer_last_name") or "Customer",
                    is_guest=True,
                )
                self.customer_repo._add_tenant_on_create(customer)
                self.session.add(customer)
                await self.session.flush()

            shipping = payload.get("shipping_address") or {}
            billing = payload.get("billing_address") or shipping
            address_defaults = {"first_name": "Marketplace", "last_name": "Customer", "line1": "N/A", "city": "N/A", "country": "US"}

            order_data = OrderCreateRequest(
                customer_id=customer.id,
                currency=payload.get("currency", DEFAULT_CURRENCY),
                billing_address=OrderAddressInput(**{**address_defaults, **billing}),
                shipping_address=OrderAddressInput(**{**address_defaults, **shipping}),
                shipping_amount=payload.get("shipping_amount", 0),
                source=f"marketplace:{connector.connector_type}",
                items=order_items,
            )
            order = await self.order_service.create_order(order_data)

            link.order_id = order.id
            link.status = MarketplaceOrderLinkStatus.imported
            link.imported_at = datetime.utcnow()
            link.last_error = None
        except Exception as exc:  # noqa: BLE001 -- one bad marketplace order shouldn't break webhook ingestion
            link.status = MarketplaceOrderLinkStatus.failed
            link.last_error = str(exc)

        return await self.order_link_repo.create(link)

    async def sync_orders(self, connector_id: str, triggered_by: str = "manual") -> MarketplaceSyncLog:
        connector = await self._get_connector_or_404(connector_id)
        adapter = get_adapter(connector.connector_type)

        payloads = await adapter.fetch_orders(since=connector.last_sync_at)

        log = MarketplaceSyncLog(marketplace_connector_id=connector.id, sync_type=MarketplaceSyncType.order, status=MarketplaceSyncStatus.success, triggered_by=triggered_by)
        log = await self.log_repo.create(log)

        for payload in payloads:
            log.items_processed += 1
            link = await self.import_order_payload(connector, payload)
            if link.status == MarketplaceOrderLinkStatus.imported:
                log.items_succeeded += 1
            else:
                log.items_failed += 1

        return await self._finish_log(log, connector)
