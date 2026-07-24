import { apiFetch } from '@/lib/api-client';
import type { MarketplaceSyncLogListResponse, MarketplaceSyncLogRead } from '@/lib/types';

export async function syncMarketplaceProducts(connectorId: string, productIds?: string[]): Promise<MarketplaceSyncLogRead> {
  return apiFetch<MarketplaceSyncLogRead>(`/api/v1/marketplace/sync/${connectorId}/products`, { method: 'POST', json: { product_ids: productIds ?? null } });
}

export async function syncMarketplaceInventory(connectorId: string, productIds?: string[]): Promise<MarketplaceSyncLogRead> {
  return apiFetch<MarketplaceSyncLogRead>(`/api/v1/marketplace/sync/${connectorId}/inventory`, { method: 'POST', json: { product_ids: productIds ?? null } });
}

export async function syncMarketplacePrices(connectorId: string, productIds?: string[]): Promise<MarketplaceSyncLogRead> {
  return apiFetch<MarketplaceSyncLogRead>(`/api/v1/marketplace/sync/${connectorId}/prices`, { method: 'POST', json: { product_ids: productIds ?? null } });
}

export async function syncMarketplaceOrders(connectorId: string): Promise<MarketplaceSyncLogRead> {
  return apiFetch<MarketplaceSyncLogRead>(`/api/v1/marketplace/sync/${connectorId}/orders`, { method: 'POST' });
}

export async function fetchMarketplaceSyncLogs(connectorId?: string, syncType?: string, limit = 50, offset = 0): Promise<MarketplaceSyncLogListResponse> {
  const params = new URLSearchParams();
  if (connectorId) params.set('connector_id', connectorId);
  if (syncType) params.set('sync_type', syncType);
  params.set('limit', String(limit));
  params.set('offset', String(offset));
  return apiFetch<MarketplaceSyncLogListResponse>(`/api/v1/marketplace/sync/logs?${params.toString()}`);
}
