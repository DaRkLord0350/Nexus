import { apiFetch } from '@/lib/api-client';
import type { CollectionItem, CollectionListResponse, CollectionRuleCondition, ProductItem } from '@/lib/types';

export interface CollectionFilters {
  status?: string;
  isFeatured?: boolean;
  q?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface CollectionCreateInput {
  name: string;
  slug?: string;
  description?: string;
  image_url?: string;
  collection_type?: string;
  rules?: CollectionRuleCondition[];
  status?: string;
  is_featured?: boolean;
  sort_order?: number;
  seo_title?: string;
  seo_description?: string;
  seo_keywords?: string;
  og_image_url?: string;
  canonical_url?: string;
  no_index?: boolean;
}

export type CollectionUpdateInput = Partial<CollectionCreateInput>;

function buildQuery(filters: CollectionFilters): string {
  const params = new URLSearchParams();
  if (filters.status) params.set('status', filters.status);
  if (filters.isFeatured !== undefined) params.set('is_featured', String(filters.isFeatured));
  if (filters.q) params.set('q', filters.q);
  params.set('sort_by', filters.sortBy ?? 'sort_order');
  params.set('sort_order', filters.sortOrder ?? 'asc');
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchCollections(filters: CollectionFilters = {}): Promise<CollectionListResponse> {
  return apiFetch<CollectionListResponse>(`/api/v1/catalog/collections/?${buildQuery(filters)}`);
}

export async function createCollection(data: CollectionCreateInput): Promise<CollectionItem> {
  return apiFetch<CollectionItem>('/api/v1/catalog/collections/', { method: 'POST', json: data });
}

export async function updateCollection(collectionId: string, data: CollectionUpdateInput): Promise<CollectionItem> {
  return apiFetch<CollectionItem>(`/api/v1/catalog/collections/${collectionId}`, { method: 'PATCH', json: data });
}

export async function deleteCollection(collectionId: string): Promise<void> {
  await apiFetch(`/api/v1/catalog/collections/${collectionId}`, { method: 'DELETE' });
}

export async function bulkDeleteCollections(ids: string[]): Promise<{ deleted_count: number }> {
  return apiFetch(`/api/v1/catalog/collections/bulk-delete`, { method: 'POST', json: { ids } });
}

export async function fetchCollectionProducts(collectionId: string): Promise<ProductItem[]> {
  return apiFetch<ProductItem[]>(`/api/v1/catalog/collections/${collectionId}/products`);
}

export async function addCollectionProducts(collectionId: string, productIds: string[]): Promise<void> {
  await apiFetch(`/api/v1/catalog/collections/${collectionId}/products`, { method: 'POST', json: { product_ids: productIds } });
}

export async function removeCollectionProducts(collectionId: string, productIds: string[]): Promise<void> {
  await apiFetch(`/api/v1/catalog/collections/${collectionId}/products`, { method: 'DELETE', json: { product_ids: productIds } });
}
