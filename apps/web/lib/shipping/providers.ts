import { apiFetch } from '@/lib/api-client';
import type { ShippingProviderListResponse, ShippingProviderRead } from '@/lib/types';

export interface ShippingProviderCreateInput {
  name: string;
  code: string;
  provider_type?: string;
  is_active?: boolean;
  is_default?: boolean;
  priority?: number;
  credentials?: Record<string, string>;
  webhook_secret?: string;
  supports_cod?: boolean;
  supports_insurance?: boolean;
  supports_reverse_pickup?: boolean;
  supports_international?: boolean;
  base_rate?: number;
  base_transit_days?: number;
}

export interface ShippingProviderUpdateInput extends Partial<ShippingProviderCreateInput> {}

export async function fetchShippingProviders(limit = 50, offset = 0): Promise<ShippingProviderListResponse> {
  return apiFetch<ShippingProviderListResponse>(`/api/v1/shipping/providers/?limit=${limit}&offset=${offset}`);
}

export async function fetchShippingProvider(providerId: string): Promise<ShippingProviderRead> {
  return apiFetch<ShippingProviderRead>(`/api/v1/shipping/providers/${providerId}`);
}

export async function createShippingProvider(data: ShippingProviderCreateInput): Promise<ShippingProviderRead> {
  return apiFetch<ShippingProviderRead>('/api/v1/shipping/providers/', { method: 'POST', json: data });
}

export async function updateShippingProvider(providerId: string, data: ShippingProviderUpdateInput): Promise<ShippingProviderRead> {
  return apiFetch<ShippingProviderRead>(`/api/v1/shipping/providers/${providerId}`, { method: 'PATCH', json: data });
}

export async function deleteShippingProvider(providerId: string): Promise<void> {
  await apiFetch(`/api/v1/shipping/providers/${providerId}`, { method: 'DELETE' });
}
