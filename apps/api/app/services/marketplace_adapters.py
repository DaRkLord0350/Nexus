"""Marketplace connector adapter abstraction.

No real marketplace API credentials or network access exist in this
environment, so each adapter below is a mock that simulates the call shape a
real integration would make (mirrors PaymentService._call_gateway's "mock
gateway" pattern). Swap the class returned by `get_adapter()` for a real
WooCommerce/Amazon SP-API/Flipkart/Shopify/Etsy/eBay client without touching
any caller — every adapter implements the same `MarketplaceAdapter` protocol.

Push operations (product/inventory/price) act on our own real data and
deterministically "succeed", assigning a mock external id/url — this is
genuinely demonstrable without any fabricated external data.

Pull operations (fetch_orders) return an empty list: there is no real
external marketplace to poll. In practice all of WooCommerce, Shopify, and
Amazon push order-created notifications via webhook rather than requiring
polling, so MarketplaceWebhookService.process_webhook (order.created events)
is the realistic, fully-testable path for order import in this codebase.
"""
from abc import ABC, abstractmethod
from typing import Any
from uuid import uuid4


class MarketplaceAdapter(ABC):
    connector_type: str = "other"

    @abstractmethod
    async def push_product(self, product: Any) -> dict:
        """Create/update a listing for `product`. Returns {external_id, external_url}."""

    @abstractmethod
    async def push_inventory(self, external_id: str, quantity: int) -> bool:
        """Push a stock quantity for an already-linked listing."""

    @abstractmethod
    async def push_price(self, external_id: str, price: float) -> bool:
        """Push a price for an already-linked listing."""

    @abstractmethod
    async def fetch_orders(self, since: Any = None) -> list[dict]:
        """Pull new orders since `since`. See module docstring: mock adapters
        return an empty list — real order import happens via webhook."""


class MockMarketplaceAdapter(MarketplaceAdapter):
    """Shared mock implementation used by every connector_type. A real
    integration would subclass per-marketplace with actual HTTP calls."""

    def __init__(self, connector_type: str):
        self.connector_type = connector_type

    async def push_product(self, product: Any) -> dict:
        external_id = f"MOCK-{self.connector_type.upper()}-{uuid4().hex[:10].upper()}"
        return {
            "external_id": external_id,
            "external_url": f"https://{self.connector_type}.example/listings/{external_id}",
        }

    async def push_inventory(self, external_id: str, quantity: int) -> bool:
        return True

    async def push_price(self, external_id: str, price: float) -> bool:
        return True

    async def fetch_orders(self, since: Any = None) -> list[dict]:
        return []


CONNECTOR_TYPES = ["woocommerce", "amazon", "flipkart", "shopify", "etsy", "ebay", "other"]


def get_adapter(connector_type: str) -> MarketplaceAdapter:
    return MockMarketplaceAdapter(connector_type)
