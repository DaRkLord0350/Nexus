import { apiFetch } from '@/lib/api-client';
import type { AttributeItem, AttributeListResponse, AttributeValueItem } from '@/lib/types';

export interface AttributeFilters {
  isActive?: boolean;
  isVariantAttribute?: boolean;
  q?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface AttributeCreateInput {
  name: string;
  code?: string;
  input_type?: string;
  is_variant_attribute?: boolean;
  sort_order?: number;
  is_active?: boolean;
}

export type AttributeUpdateInput = Partial<AttributeCreateInput>;

export interface AttributeValueCreateInput {
  value: string;
  slug?: string;
  color_hex?: string;
  sort_order?: number;
  is_active?: boolean;
}

export type AttributeValueUpdateInput = Partial<AttributeValueCreateInput>;

function buildQuery(filters: AttributeFilters): string {
  const params = new URLSearchParams();
  if (filters.isActive !== undefined) params.set('is_active', String(filters.isActive));
  if (filters.isVariantAttribute !== undefined) params.set('is_variant_attribute', String(filters.isVariantAttribute));
  if (filters.q) params.set('q', filters.q);
  params.set('sort_by', filters.sortBy ?? 'sort_order');
  params.set('sort_order', filters.sortOrder ?? 'asc');
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchAttributes(filters: AttributeFilters = {}): Promise<AttributeListResponse> {
  return apiFetch<AttributeListResponse>(`/api/v1/catalog/attributes/?${buildQuery(filters)}`);
}

export async function createAttribute(data: AttributeCreateInput): Promise<AttributeItem> {
  return apiFetch<AttributeItem>('/api/v1/catalog/attributes/', { method: 'POST', json: data });
}

export async function updateAttribute(attributeId: string, data: AttributeUpdateInput): Promise<AttributeItem> {
  return apiFetch<AttributeItem>(`/api/v1/catalog/attributes/${attributeId}`, { method: 'PATCH', json: data });
}

export async function deleteAttribute(attributeId: string): Promise<void> {
  await apiFetch(`/api/v1/catalog/attributes/${attributeId}`, { method: 'DELETE' });
}

export async function bulkDeleteAttributes(ids: string[]): Promise<{ deleted_count: number }> {
  return apiFetch(`/api/v1/catalog/attributes/bulk-delete`, { method: 'POST', json: { ids } });
}

export async function fetchAttributeValues(attributeId: string): Promise<AttributeValueItem[]> {
  return apiFetch<AttributeValueItem[]>(`/api/v1/catalog/attributes/${attributeId}/values`);
}

export async function createAttributeValue(attributeId: string, data: AttributeValueCreateInput): Promise<AttributeValueItem> {
  return apiFetch<AttributeValueItem>(`/api/v1/catalog/attributes/${attributeId}/values`, { method: 'POST', json: data });
}

export async function updateAttributeValue(attributeId: string, valueId: string, data: AttributeValueUpdateInput): Promise<AttributeValueItem> {
  return apiFetch<AttributeValueItem>(`/api/v1/catalog/attributes/${attributeId}/values/${valueId}`, { method: 'PATCH', json: data });
}

export async function deleteAttributeValue(attributeId: string, valueId: string): Promise<void> {
  await apiFetch(`/api/v1/catalog/attributes/${attributeId}/values/${valueId}`, { method: 'DELETE' });
}
