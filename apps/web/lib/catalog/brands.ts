import { apiFetch } from '@/lib/api-client';
import type { BrandItem, BrandListResponse } from '@/lib/types';

export interface BrandFilters {
  status?: string;
  isFeatured?: boolean;
  q?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface BrandCreateInput {
  name: string;
  slug?: string;
  description?: string;
  logo_url?: string;
  website?: string;
  is_featured?: boolean;
  status?: string;
  seo_title?: string;
  seo_description?: string;
  seo_keywords?: string;
  og_image_url?: string;
  canonical_url?: string;
  no_index?: boolean;
}

export type BrandUpdateInput = Partial<BrandCreateInput>;

function buildQuery(filters: BrandFilters): string {
  const params = new URLSearchParams();
  if (filters.status) params.set('status', filters.status);
  if (filters.isFeatured !== undefined) params.set('is_featured', String(filters.isFeatured));
  if (filters.q) params.set('q', filters.q);
  params.set('sort_by', filters.sortBy ?? 'name');
  params.set('sort_order', filters.sortOrder ?? 'asc');
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchBrands(filters: BrandFilters = {}): Promise<BrandListResponse> {
  return apiFetch<BrandListResponse>(`/api/v1/catalog/brands/?${buildQuery(filters)}`);
}

export async function fetchBrand(brandId: string): Promise<BrandItem> {
  return apiFetch<BrandItem>(`/api/v1/catalog/brands/${brandId}`);
}

export async function createBrand(data: BrandCreateInput): Promise<BrandItem> {
  return apiFetch<BrandItem>('/api/v1/catalog/brands/', { method: 'POST', json: data });
}

export async function updateBrand(brandId: string, data: BrandUpdateInput): Promise<BrandItem> {
  return apiFetch<BrandItem>(`/api/v1/catalog/brands/${brandId}`, { method: 'PATCH', json: data });
}

export async function deleteBrand(brandId: string): Promise<void> {
  await apiFetch(`/api/v1/catalog/brands/${brandId}`, { method: 'DELETE' });
}

export async function bulkDeleteBrands(ids: string[]): Promise<{ deleted_count: number }> {
  return apiFetch(`/api/v1/catalog/brands/bulk-delete`, { method: 'POST', json: { ids } });
}

export async function restoreBrand(brandId: string): Promise<BrandItem> {
  return apiFetch<BrandItem>(`/api/v1/catalog/brands/${brandId}/restore`, { method: 'POST' });
}
