import { apiFetch } from '@/lib/api-client';
import type { CategoryBreadcrumbItem, CategoryItem, CategoryListResponse, CategoryTreeNode } from '@/lib/types';

export interface CategoryFilters {
  parentId?: string | null;
  rootOnly?: boolean;
  status?: string;
  isFeatured?: boolean;
  isVisible?: boolean;
  q?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface CategoryCreateInput {
  name: string;
  slug?: string;
  description?: string;
  parent_id?: string | null;
  image_url?: string;
  banner_url?: string;
  sort_order?: number;
  is_featured?: boolean;
  is_visible?: boolean;
  status?: string;
  seo_title?: string;
  seo_description?: string;
  seo_keywords?: string;
  og_image_url?: string;
  canonical_url?: string;
  no_index?: boolean;
}

export type CategoryUpdateInput = Partial<CategoryCreateInput> & { move_to_root?: boolean };

function buildQuery(filters: CategoryFilters): string {
  const params = new URLSearchParams();
  if (filters.parentId !== undefined) params.set('parent_id', filters.parentId ?? '');
  if (filters.rootOnly) params.set('root_only', 'true');
  if (filters.status) params.set('status', filters.status);
  if (filters.isFeatured !== undefined) params.set('is_featured', String(filters.isFeatured));
  if (filters.isVisible !== undefined) params.set('is_visible', String(filters.isVisible));
  if (filters.q) params.set('q', filters.q);
  params.set('sort_by', filters.sortBy ?? 'sort_order');
  params.set('sort_order', filters.sortOrder ?? 'asc');
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchCategories(filters: CategoryFilters = {}): Promise<CategoryListResponse> {
  return apiFetch<CategoryListResponse>(`/api/v1/catalog/categories/?${buildQuery(filters)}`);
}

export async function fetchCategoryTree(parentId?: string | null): Promise<CategoryTreeNode[]> {
  const params = new URLSearchParams();
  if (parentId) params.set('parent_id', parentId);
  return apiFetch<CategoryTreeNode[]>(`/api/v1/catalog/categories/tree?${params.toString()}`);
}

export async function fetchCategory(categoryId: string): Promise<CategoryItem> {
  return apiFetch<CategoryItem>(`/api/v1/catalog/categories/${categoryId}`);
}

export async function fetchCategoryBreadcrumbs(categoryId: string): Promise<CategoryBreadcrumbItem[]> {
  return apiFetch<CategoryBreadcrumbItem[]>(`/api/v1/catalog/categories/${categoryId}/breadcrumbs`);
}

export async function createCategory(data: CategoryCreateInput): Promise<CategoryItem> {
  return apiFetch<CategoryItem>('/api/v1/catalog/categories/', { method: 'POST', json: data });
}

export async function updateCategory(categoryId: string, data: CategoryUpdateInput): Promise<CategoryItem> {
  return apiFetch<CategoryItem>(`/api/v1/catalog/categories/${categoryId}`, { method: 'PATCH', json: data });
}

export async function deleteCategory(categoryId: string, cascade = false): Promise<void> {
  await apiFetch(`/api/v1/catalog/categories/${categoryId}?cascade=${cascade}`, { method: 'DELETE' });
}

export async function restoreCategory(categoryId: string): Promise<CategoryItem> {
  return apiFetch<CategoryItem>(`/api/v1/catalog/categories/${categoryId}/restore`, { method: 'POST' });
}
