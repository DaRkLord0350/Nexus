import { apiFetch } from '@/lib/api-client';
import type { ProductTypeAttributeItem, ProductTypeItem, ProductTypeListResponse } from '@/lib/types';

export interface ProductTypeCreateInput {
  name: string;
  slug?: string;
  description?: string;
  is_active?: boolean;
}

export type ProductTypeUpdateInput = Partial<ProductTypeCreateInput>;

export interface ProductTypeAttributeConfig {
  attribute_id: string;
  is_required?: boolean;
  sort_order?: number;
}

export async function fetchProductTypes(q?: string): Promise<ProductTypeListResponse> {
  const params = new URLSearchParams({ limit: '200' });
  if (q) params.set('q', q);
  return apiFetch<ProductTypeListResponse>(`/api/v1/catalog/product-types/?${params.toString()}`);
}

export async function createProductType(data: ProductTypeCreateInput): Promise<ProductTypeItem> {
  return apiFetch<ProductTypeItem>('/api/v1/catalog/product-types/', { method: 'POST', json: data });
}

export async function updateProductType(id: string, data: ProductTypeUpdateInput): Promise<ProductTypeItem> {
  return apiFetch<ProductTypeItem>(`/api/v1/catalog/product-types/${id}`, { method: 'PATCH', json: data });
}

export async function deleteProductType(id: string): Promise<void> {
  await apiFetch(`/api/v1/catalog/product-types/${id}`, { method: 'DELETE' });
}

export async function fetchProductTypeAttributes(id: string): Promise<ProductTypeAttributeItem[]> {
  return apiFetch<ProductTypeAttributeItem[]>(`/api/v1/catalog/product-types/${id}/attributes`);
}

export async function setProductTypeAttributes(id: string, attributes: ProductTypeAttributeConfig[]): Promise<void> {
  await apiFetch(`/api/v1/catalog/product-types/${id}/attributes`, { method: 'PUT', json: { attributes } });
}
