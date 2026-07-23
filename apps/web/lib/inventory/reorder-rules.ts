import { apiFetch } from '@/lib/api-client';
import type { ReorderRuleItem, ReorderRuleListResponse } from '@/lib/types';

export interface ReorderRuleFilters {
  warehouseId?: string;
  productId?: string;
  isActive?: boolean;
  limit?: number;
  offset?: number;
}

export interface ReorderRuleCreateInput {
  product_id: string;
  variant_id?: string;
  warehouse_id: string;
  minimum_stock: number;
  maximum_stock?: number;
  reorder_quantity: number;
  supplier_name?: string;
  lead_time_days?: number;
  is_active?: boolean;
}

export interface ReorderRuleUpdateInput {
  minimum_stock?: number;
  maximum_stock?: number;
  reorder_quantity?: number;
  supplier_name?: string;
  lead_time_days?: number;
  is_active?: boolean;
}

function buildQuery(filters: ReorderRuleFilters): string {
  const params = new URLSearchParams();
  if (filters.warehouseId) params.set('warehouse_id', filters.warehouseId);
  if (filters.productId) params.set('product_id', filters.productId);
  if (filters.isActive !== undefined) params.set('is_active', String(filters.isActive));
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchReorderRules(filters: ReorderRuleFilters = {}): Promise<ReorderRuleListResponse> {
  return apiFetch<ReorderRuleListResponse>(`/api/v1/inventory/reorder-rules/?${buildQuery(filters)}`);
}

export async function createReorderRule(data: ReorderRuleCreateInput): Promise<ReorderRuleItem> {
  return apiFetch<ReorderRuleItem>('/api/v1/inventory/reorder-rules/', { method: 'POST', json: data });
}

export async function updateReorderRule(ruleId: string, data: ReorderRuleUpdateInput): Promise<ReorderRuleItem> {
  return apiFetch<ReorderRuleItem>(`/api/v1/inventory/reorder-rules/${ruleId}`, { method: 'PATCH', json: data });
}

export async function deleteReorderRule(ruleId: string): Promise<void> {
  await apiFetch(`/api/v1/inventory/reorder-rules/${ruleId}`, { method: 'DELETE' });
}

export async function bulkDeleteReorderRules(ids: string[]): Promise<{ deleted_count: number }> {
  return apiFetch(`/api/v1/inventory/reorder-rules/bulk-delete`, { method: 'POST', json: { ids } });
}
