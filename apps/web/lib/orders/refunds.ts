import { apiFetch } from '@/lib/api-client';
import type { RefundDetail, RefundListResponse, RefundMethod } from '@/lib/types';

export interface RefundFilters {
  orderId?: string;
  customerId?: string;
  status?: string;
  q?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface RefundCreateInput {
  order_id: string;
  return_request_id?: string;
  method?: RefundMethod;
  amount: number;
  reason?: string;
}

function buildQuery(filters: RefundFilters): string {
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

export async function fetchRefunds(filters: RefundFilters = {}): Promise<RefundListResponse> {
  return apiFetch<RefundListResponse>(`/api/v1/refunds/?${buildQuery(filters)}`);
}

export async function fetchRefund(refundId: string): Promise<RefundDetail> {
  return apiFetch<RefundDetail>(`/api/v1/refunds/${refundId}`);
}

export async function createRefund(data: RefundCreateInput): Promise<RefundDetail> {
  return apiFetch<RefundDetail>('/api/v1/refunds/', { method: 'POST', json: data });
}

export async function approveRefund(refundId: string) {
  return apiFetch(`/api/v1/refunds/${refundId}/approve`, { method: 'POST' });
}

export async function rejectRefund(refundId: string, reason?: string) {
  return apiFetch(`/api/v1/refunds/${refundId}/reject`, { method: 'POST', json: { reason } });
}

export async function completeRefund(refundId: string) {
  return apiFetch(`/api/v1/refunds/${refundId}/complete`, { method: 'POST' });
}

export async function failRefund(refundId: string, reason?: string) {
  return apiFetch(`/api/v1/refunds/${refundId}/fail`, { method: 'POST', json: { reason } });
}
