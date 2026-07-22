import { apiFetch } from '@/lib/api-client';
import type { BatchItem, BatchListResponse } from '@/lib/types';

export interface BatchFilters {
  productId?: string;
  warehouseId?: string;
  status?: string;
  q?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface BatchCreateInput {
  product_id: string;
  variant_id?: string;
  warehouse_id: string;
  batch_number: string;
  manufactured_date?: string;
  expiry_date?: string;
  received_quantity?: number;
  cost_price?: number;
  status?: string;
}

export interface BatchUpdateInput {
  manufactured_date?: string;
  expiry_date?: string;
  remaining_quantity?: number;
  cost_price?: number;
  status?: string;
}

function buildQuery(filters: BatchFilters): string {
  const params = new URLSearchParams();
  if (filters.productId) params.set('product_id', filters.productId);
  if (filters.warehouseId) params.set('warehouse_id', filters.warehouseId);
  if (filters.status) params.set('status', filters.status);
  if (filters.q) params.set('q', filters.q);
  params.set('sort_by', filters.sortBy ?? 'expiry_date');
  params.set('sort_order', filters.sortOrder ?? 'asc');
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchBatches(filters: BatchFilters = {}): Promise<BatchListResponse> {
  return apiFetch<BatchListResponse>(`/api/v1/inventory/batches/?${buildQuery(filters)}`);
}

export async function createBatch(data: BatchCreateInput): Promise<BatchItem> {
  return apiFetch<BatchItem>('/api/v1/inventory/batches/', { method: 'POST', json: data });
}

export async function updateBatch(batchId: string, data: BatchUpdateInput): Promise<BatchItem> {
  return apiFetch<BatchItem>(`/api/v1/inventory/batches/${batchId}`, { method: 'PATCH', json: data });
}

export async function deleteBatch(batchId: string): Promise<void> {
  await apiFetch(`/api/v1/inventory/batches/${batchId}`, { method: 'DELETE' });
}

export async function bulkDeleteBatches(ids: string[]): Promise<{ deleted_count: number }> {
  return apiFetch(`/api/v1/inventory/batches/bulk-delete`, { method: 'POST', json: { ids } });
}
