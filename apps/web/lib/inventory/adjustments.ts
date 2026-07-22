import { apiFetch } from '@/lib/api-client';
import type { StockAdjustmentItem, StockAdjustmentListResponse } from '@/lib/types';

export interface StockAdjustmentFilters {
  warehouseId?: string;
  productId?: string;
  reason?: string;
  limit?: number;
  offset?: number;
}

export interface StockAdjustmentCreateInput {
  adjustment_number?: string;
  product_id: string;
  variant_id?: string;
  warehouse_id: string;
  bin_id?: string;
  quantity_delta: number;
  reason?: string;
  notes?: string;
}

function buildQuery(filters: StockAdjustmentFilters): string {
  const params = new URLSearchParams();
  if (filters.warehouseId) params.set('warehouse_id', filters.warehouseId);
  if (filters.productId) params.set('product_id', filters.productId);
  if (filters.reason) params.set('reason', filters.reason);
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchAdjustments(filters: StockAdjustmentFilters = {}): Promise<StockAdjustmentListResponse> {
  return apiFetch<StockAdjustmentListResponse>(`/api/v1/inventory/adjustments/?${buildQuery(filters)}`);
}

export async function createAdjustment(data: StockAdjustmentCreateInput): Promise<StockAdjustmentItem> {
  return apiFetch<StockAdjustmentItem>('/api/v1/inventory/adjustments/', { method: 'POST', json: data });
}
