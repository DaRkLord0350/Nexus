import { apiFetch } from '@/lib/api-client';
import type { MarketplaceProductLinkListResponse } from '@/lib/types';

export async function fetchMarketplaceProductLinks(connectorId?: string, syncStatus?: string, limit = 50, offset = 0): Promise<MarketplaceProductLinkListResponse> {
  const params = new URLSearchParams();
  if (connectorId) params.set('connector_id', connectorId);
  if (syncStatus) params.set('sync_status', syncStatus);
  params.set('limit', String(limit));
  params.set('offset', String(offset));
  return apiFetch<MarketplaceProductLinkListResponse>(`/api/v1/marketplace/products/links?${params.toString()}`);
}
