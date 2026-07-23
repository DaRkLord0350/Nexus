import { apiFetch } from '@/lib/api-client';
import type { ReturnItemCondition, ReturnRequestDetail, ReturnRequestListResponse, ReturnResolution } from '@/lib/types';

export interface ReturnFilters {
  orderId?: string;
  customerId?: string;
  status?: string;
  q?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface ReturnItemInput {
  order_item_id: string;
  quantity: number;
  reason_code?: string;
  image_urls?: string[];
}

export interface ReturnCreateInput {
  order_id: string;
  reason_code: string;
  reason_notes?: string;
  items: ReturnItemInput[];
}

function buildQuery(filters: ReturnFilters): string {
  const params = new URLSearchParams();
  if (filters.orderId) params.set('order_id', filters.orderId);
  if (filters.customerId) params.set('customer_id', filters.customerId);
  if (filters.status) params.set('status', filters.status);
  if (filters.q) params.set('q', filters.q);
  params.set('sort_by', filters.sortBy ?? 'created_at');
  params.set('sort_order', filters.sortOrder ?? 'desc');
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchReturns(filters: ReturnFilters = {}): Promise<ReturnRequestListResponse> {
  return apiFetch<ReturnRequestListResponse>(`/api/v1/returns/?${buildQuery(filters)}`);
}

export async function fetchReturn(returnId: string): Promise<ReturnRequestDetail> {
  return apiFetch<ReturnRequestDetail>(`/api/v1/returns/${returnId}`);
}

export async function createReturn(data: ReturnCreateInput): Promise<ReturnRequestDetail> {
  return apiFetch<ReturnRequestDetail>('/api/v1/returns/', { method: 'POST', json: data });
}

export async function approveReturn(returnId: string, resolution?: ReturnResolution): Promise<ReturnRequestDetail> {
  return apiFetch(`/api/v1/returns/${returnId}/approve`, { method: 'POST', json: { resolution } });
}

export async function rejectReturn(returnId: string, reason?: string): Promise<ReturnRequestDetail> {
  return apiFetch(`/api/v1/returns/${returnId}/reject`, { method: 'POST', json: { reason } });
}

export async function receiveReturn(returnId: string, warehouseId?: string): Promise<ReturnRequestDetail> {
  return apiFetch(`/api/v1/returns/${returnId}/receive`, { method: 'POST', json: { warehouse_id: warehouseId } });
}

export async function startReturnInspection(returnId: string): Promise<ReturnRequestDetail> {
  return apiFetch(`/api/v1/returns/${returnId}/inspect`, { method: 'POST' });
}

export async function inspectReturnItem(returnId: string, itemId: string, condition: ReturnItemCondition, reasonCode?: string) {
  return apiFetch(`/api/v1/returns/${returnId}/items/${itemId}/inspection`, { method: 'PATCH', json: { condition, reason_code: reasonCode } });
}

export async function completeReturn(returnId: string, resolution: ReturnResolution, restock = true): Promise<ReturnRequestDetail> {
  return apiFetch(`/api/v1/returns/${returnId}/complete`, { method: 'POST', json: { resolution, restock } });
}

export async function cancelReturn(returnId: string, reason?: string): Promise<ReturnRequestDetail> {
  return apiFetch(`/api/v1/returns/${returnId}/cancel`, { method: 'POST', json: { reason } });
}
