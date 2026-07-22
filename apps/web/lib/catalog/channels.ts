import { apiFetch } from '@/lib/api-client';
import type { ChannelItem, ChannelListResponse, ProductChannelItem } from '@/lib/types';

export interface ChannelCreateInput {
  name: string;
  code?: string;
  channel_type?: string;
  is_active?: boolean;
  is_default?: boolean;
}

export type ChannelUpdateInput = Partial<ChannelCreateInput>;

export async function fetchChannels(isActive?: boolean): Promise<ChannelListResponse> {
  const params = new URLSearchParams({ limit: '200' });
  if (isActive !== undefined) params.set('is_active', String(isActive));
  return apiFetch<ChannelListResponse>(`/api/v1/catalog/channels/?${params.toString()}`);
}

export async function createChannel(data: ChannelCreateInput): Promise<ChannelItem> {
  return apiFetch<ChannelItem>('/api/v1/catalog/channels/', { method: 'POST', json: data });
}

export async function updateChannel(id: string, data: ChannelUpdateInput): Promise<ChannelItem> {
  return apiFetch<ChannelItem>(`/api/v1/catalog/channels/${id}`, { method: 'PATCH', json: data });
}

export async function deleteChannel(id: string): Promise<void> {
  await apiFetch(`/api/v1/catalog/channels/${id}`, { method: 'DELETE' });
}

export async function fetchProductChannels(productId: string): Promise<ProductChannelItem[]> {
  return apiFetch<ProductChannelItem[]>(`/api/v1/catalog/products/${productId}/channels/`);
}

export async function setProductChannels(productId: string, channelIds: string[]): Promise<void> {
  await apiFetch(`/api/v1/catalog/products/${productId}/channels/`, { method: 'PUT', json: { channel_ids: channelIds } });
}
