import { apiFetch } from '@/lib/api-client';
import type { MarketplaceConnectorListResponse, MarketplaceConnectorRead } from '@/lib/types';

export interface MarketplaceConnectorCreateInput {
  name: string;
  code: string;
  connector_type?: string;
  is_active?: boolean;
  credentials?: Record<string, string>;
  webhook_secret?: string;
  store_url?: string;
  auto_sync_products?: boolean;
  auto_sync_orders?: boolean;
  auto_sync_inventory?: boolean;
  auto_sync_prices?: boolean;
  sync_interval_minutes?: number;
}

export interface MarketplaceConnectorUpdateInput extends Partial<MarketplaceConnectorCreateInput> {}

export async function fetchMarketplaceConnectors(limit = 50, offset = 0): Promise<MarketplaceConnectorListResponse> {
  return apiFetch<MarketplaceConnectorListResponse>(`/api/v1/marketplace/connectors/?limit=${limit}&offset=${offset}`);
}

export async function fetchMarketplaceConnector(connectorId: string): Promise<MarketplaceConnectorRead> {
  return apiFetch<MarketplaceConnectorRead>(`/api/v1/marketplace/connectors/${connectorId}`);
}

export async function createMarketplaceConnector(data: MarketplaceConnectorCreateInput): Promise<MarketplaceConnectorRead> {
  return apiFetch<MarketplaceConnectorRead>('/api/v1/marketplace/connectors/', { method: 'POST', json: data });
}

export async function updateMarketplaceConnector(connectorId: string, data: MarketplaceConnectorUpdateInput): Promise<MarketplaceConnectorRead> {
  return apiFetch<MarketplaceConnectorRead>(`/api/v1/marketplace/connectors/${connectorId}`, { method: 'PATCH', json: data });
}

export async function deleteMarketplaceConnector(connectorId: string): Promise<void> {
  await apiFetch(`/api/v1/marketplace/connectors/${connectorId}`, { method: 'DELETE' });
}
