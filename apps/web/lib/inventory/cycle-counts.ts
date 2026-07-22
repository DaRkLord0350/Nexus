import { apiFetch } from '@/lib/api-client';
import type { CycleCountDetail, CycleCountItem, CycleCountLineItem, CycleCountListResponse } from '@/lib/types';

export interface CycleCountFilters {
  warehouseId?: string;
  status?: string;
  q?: string;
  limit?: number;
  offset?: number;
}

export interface CycleCountItemInput {
  product_id: string;
  variant_id?: string;
  bin_id?: string;
  notes?: string;
}

export interface CycleCountCreateInput {
  count_number?: string;
  warehouse_id: string;
  zone_id?: string;
  scheduled_date?: string;
  assigned_to?: string;
  notes?: string;
  items?: CycleCountItemInput[];
}

function buildQuery(filters: CycleCountFilters): string {
  const params = new URLSearchParams();
  if (filters.warehouseId) params.set('warehouse_id', filters.warehouseId);
  if (filters.status) params.set('status', filters.status);
  if (filters.q) params.set('q', filters.q);
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchCycleCounts(filters: CycleCountFilters = {}): Promise<CycleCountListResponse> {
  return apiFetch<CycleCountListResponse>(`/api/v1/inventory/cycle-counts/?${buildQuery(filters)}`);
}

export async function fetchCycleCount(cycleCountId: string): Promise<CycleCountDetail> {
  return apiFetch<CycleCountDetail>(`/api/v1/inventory/cycle-counts/${cycleCountId}`);
}

export async function createCycleCount(data: CycleCountCreateInput): Promise<CycleCountItem> {
  return apiFetch<CycleCountItem>('/api/v1/inventory/cycle-counts/', { method: 'POST', json: data });
}

export async function recordCycleCountItem(cycleCountId: string, itemId: string, actualQuantity: number, notes?: string): Promise<CycleCountLineItem> {
  return apiFetch<CycleCountLineItem>(`/api/v1/inventory/cycle-counts/${cycleCountId}/items/${itemId}`, {
    method: 'PATCH',
    json: { actual_quantity: actualQuantity, notes },
  });
}

export async function completeCycleCount(cycleCountId: string): Promise<CycleCountItem> {
  return apiFetch<CycleCountItem>(`/api/v1/inventory/cycle-counts/${cycleCountId}/complete`, { method: 'POST' });
}

export async function cancelCycleCount(cycleCountId: string): Promise<CycleCountItem> {
  return apiFetch<CycleCountItem>(`/api/v1/inventory/cycle-counts/${cycleCountId}/cancel`, { method: 'POST' });
}
