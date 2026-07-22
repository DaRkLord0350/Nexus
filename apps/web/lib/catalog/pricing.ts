import { apiFetch } from '@/lib/api-client';
import type { ProductPriceItem, ProductPriceListResponse } from '@/lib/types';

export interface ProductPriceCreateInput {
  product_id: string;
  variant_id?: string | null;
  currency: string;
  mrp?: number;
  selling_price: number;
  cost_price?: number;
  compare_price?: number;
  min_price?: number;
  max_price?: number;
  customer_group?: string;
  region?: string;
  effective_from?: string;
  effective_to?: string;
  is_active?: boolean;
}

export type ProductPriceUpdateInput = Partial<Omit<ProductPriceCreateInput, 'product_id' | 'variant_id'>>;

export async function fetchPrices(productId: string, variantId?: string): Promise<ProductPriceListResponse> {
  const params = new URLSearchParams({ product_id: productId });
  if (variantId) params.set('variant_id', variantId);
  return apiFetch<ProductPriceListResponse>(`/api/v1/catalog/pricing/?${params.toString()}`);
}

export async function createPrice(data: ProductPriceCreateInput): Promise<ProductPriceItem> {
  return apiFetch<ProductPriceItem>('/api/v1/catalog/pricing/', { method: 'POST', json: data });
}

export async function updatePrice(priceId: string, data: ProductPriceUpdateInput): Promise<ProductPriceItem> {
  return apiFetch<ProductPriceItem>(`/api/v1/catalog/pricing/${priceId}`, { method: 'PATCH', json: data });
}

export async function deletePrice(priceId: string): Promise<void> {
  await apiFetch(`/api/v1/catalog/pricing/${priceId}`, { method: 'DELETE' });
}
