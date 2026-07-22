import { apiFetch } from '@/lib/api-client';
import type { VariantItem, VariantListResponse } from '@/lib/types';

export interface VariantCreateInput {
  sku: string;
  barcode?: string;
  weight?: number;
  weight_unit?: string;
  status?: string;
  is_default?: boolean;
  sort_order?: number;
  attribute_value_ids?: string[];
}

export type VariantUpdateInput = Partial<VariantCreateInput>;

export async function fetchVariants(productId: string): Promise<VariantListResponse> {
  return apiFetch<VariantListResponse>(`/api/v1/catalog/products/${productId}/variants/?limit=200`);
}

export async function createVariant(productId: string, data: VariantCreateInput): Promise<VariantItem> {
  return apiFetch<VariantItem>(`/api/v1/catalog/products/${productId}/variants/`, { method: 'POST', json: data });
}

export async function updateVariant(productId: string, variantId: string, data: VariantUpdateInput): Promise<VariantItem> {
  return apiFetch<VariantItem>(`/api/v1/catalog/products/${productId}/variants/${variantId}`, { method: 'PATCH', json: data });
}

export async function setDefaultVariant(productId: string, variantId: string): Promise<VariantItem> {
  return apiFetch<VariantItem>(`/api/v1/catalog/products/${productId}/variants/${variantId}/set-default`, { method: 'POST' });
}

export async function deleteVariant(productId: string, variantId: string): Promise<void> {
  await apiFetch(`/api/v1/catalog/products/${productId}/variants/${variantId}`, { method: 'DELETE' });
}
