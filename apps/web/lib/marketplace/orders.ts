import { apiFetch } from '@/lib/api-client';
import type { MarketplaceOrderLinkListResponse } from '@/lib/types';

export async function fetchMarketplaceOrderLinks(connectorId?: string, status?: string, limit = 50, offset = 0): Promise<MarketplaceOrderLinkListResponse> {
  const params = new URLSearchParams();
  if (connectorId) params.set('connector_id', connectorId);
  if (status) params.set('status', status);
  params.set('limit', String(limit));
  params.set('offset', String(offset));
  return apiFetch<MarketplaceOrderLinkListResponse>(`/api/v1/marketplace/orders/links?${params.toString()}`);
}
