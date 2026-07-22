import { apiFetch } from '@/lib/api-client';
import type { ProductItem, ProductListResponse } from '@/lib/types';

export interface ProductFilters {
  status?: string;
  brandId?: string;
  categoryId?: string;
  isFeatured?: boolean;
  hasVariants?: boolean;
  tagId?: string;
  q?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface ProductCreateInput {
  name: string;
  slug?: string;
  sku: string;
  barcode?: string;
  brand_id?: string | null;
  category_id?: string | null;
  tax_class_id?: string | null;
  product_type_id?: string | null;
  description?: string;
  short_description?: string;
  status?: string;
  seo_title?: string;
  seo_description?: string;
  seo_keywords?: string;
  og_image_url?: string;
  canonical_url?: string;
  no_index?: boolean;
  length?: number;
  width?: number;
  height?: number;
  dimension_unit?: string;
  weight?: number;
  weight_unit?: string;
  origin_country?: string;
  vendor?: string;
  tag_names?: string[];
  search_keywords?: string;
  track_inventory?: boolean;
  allow_backorders?: boolean;
  has_variants?: boolean;
  is_featured?: boolean;
}

export type ProductUpdateInput = Partial<ProductCreateInput>;

function buildQuery(filters: ProductFilters): string {
  const params = new URLSearchParams();
  if (filters.status) params.set('status', filters.status);
  if (filters.brandId) params.set('brand_id', filters.brandId);
  if (filters.categoryId) params.set('category_id', filters.categoryId);
  if (filters.isFeatured !== undefined) params.set('is_featured', String(filters.isFeatured));
  if (filters.hasVariants !== undefined) params.set('has_variants', String(filters.hasVariants));
  if (filters.tagId) params.set('tag_id', filters.tagId);
  if (filters.q) params.set('q', filters.q);
  params.set('sort_by', filters.sortBy ?? 'created_at');
  params.set('sort_order', filters.sortOrder ?? 'desc');
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchProducts(filters: ProductFilters = {}): Promise<ProductListResponse> {
  return apiFetch<ProductListResponse>(`/api/v1/catalog/products/?${buildQuery(filters)}`);
}

export async function fetchProduct(productId: string): Promise<ProductItem> {
  return apiFetch<ProductItem>(`/api/v1/catalog/products/${productId}`);
}

export async function createProduct(data: ProductCreateInput): Promise<ProductItem> {
  return apiFetch<ProductItem>('/api/v1/catalog/products/', { method: 'POST', json: data });
}

export async function updateProduct(productId: string, data: ProductUpdateInput): Promise<ProductItem> {
  return apiFetch<ProductItem>(`/api/v1/catalog/products/${productId}`, { method: 'PATCH', json: data });
}

export async function publishProduct(productId: string): Promise<ProductItem> {
  return apiFetch<ProductItem>(`/api/v1/catalog/products/${productId}/publish`, { method: 'POST' });
}

export async function archiveProduct(productId: string): Promise<ProductItem> {
  return apiFetch<ProductItem>(`/api/v1/catalog/products/${productId}/archive`, { method: 'POST' });
}

export async function deleteProduct(productId: string): Promise<void> {
  await apiFetch(`/api/v1/catalog/products/${productId}`, { method: 'DELETE' });
}

export async function bulkDeleteProducts(ids: string[]): Promise<{ deleted_count: number }> {
  return apiFetch(`/api/v1/catalog/products/bulk-delete`, { method: 'POST', json: { ids } });
}

export async function bulkUpdateProductStatus(ids: string[], status: string): Promise<{ updated_count: number }> {
  return apiFetch(`/api/v1/catalog/products/bulk-status`, { method: 'POST', json: { ids, status } });
}

export async function restoreProduct(productId: string): Promise<ProductItem> {
  return apiFetch<ProductItem>(`/api/v1/catalog/products/${productId}/restore`, { method: 'POST' });
}
