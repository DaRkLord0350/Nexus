import { apiFetch } from '@/lib/api-client';
import type { MarketplaceWebhookEventListResponse, MarketplaceWebhookEventRead } from '@/lib/types';

export async function fetchMarketplaceWebhookEvents(connectorId?: string, status?: string, limit = 50, offset = 0): Promise<MarketplaceWebhookEventListResponse> {
  const params = new URLSearchParams();
  if (connectorId) params.set('connector_id', connectorId);
  if (status) params.set('status', status);
  params.set('limit', String(limit));
  params.set('offset', String(offset));
  return apiFetch<MarketplaceWebhookEventListResponse>(`/api/v1/marketplace/webhooks/events?${params.toString()}`);
}

export async function retryMarketplaceWebhookEvents(connectorId?: string): Promise<MarketplaceWebhookEventRead[]> {
  const params = new URLSearchParams();
  if (connectorId) params.set('connector_id', connectorId);
  return apiFetch<MarketplaceWebhookEventRead[]>(`/api/v1/marketplace/webhooks/retry?${params.toString()}`, { method: 'POST' });
}
