import { apiFetch } from '@/lib/api-client';
import type { StockTransferDetail, StockTransferItem, StockTransferLineItem, StockTransferListResponse } from '@/lib/types';

export interface StockTransferFilters {
  fromWarehouseId?: string;
  toWarehouseId?: string;
  status?: string;
  q?: string;
  limit?: number;
  offset?: number;
}

export interface StockTransferLineItemInput {
  product_id: string;
  variant_id?: string;
  quantity_requested: number;
  notes?: string;
}

export interface StockTransferCreateInput {
  transfer_number?: string;
  from_warehouse_id: string;
  to_warehouse_id: string;
  notes?: string;
  items?: StockTransferLineItemInput[];
}

function buildQuery(filters: StockTransferFilters): string {
  const params = new URLSearchParams();
  if (filters.fromWarehouseId) params.set('from_warehouse_id', filters.fromWarehouseId);
  if (filters.toWarehouseId) params.set('to_warehouse_id', filters.toWarehouseId);
  if (filters.status) params.set('status', filters.status);
  if (filters.q) params.set('q', filters.q);
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchTransfers(filters: StockTransferFilters = {}): Promise<StockTransferListResponse> {
  return apiFetch<StockTransferListResponse>(`/api/v1/inventory/transfers/?${buildQuery(filters)}`);
}

export async function fetchTransfer(transferId: string): Promise<StockTransferDetail> {
  return apiFetch<StockTransferDetail>(`/api/v1/inventory/transfers/${transferId}`);
}

export async function createTransfer(data: StockTransferCreateInput): Promise<StockTransferItem> {
  return apiFetch<StockTransferItem>('/api/v1/inventory/transfers/', { method: 'POST', json: data });
}

export async function packTransfer(transferId: string): Promise<StockTransferItem> {
  return apiFetch<StockTransferItem>(`/api/v1/inventory/transfers/${transferId}/pack`, { method: 'POST' });
}

export async function shipTransfer(transferId: string): Promise<StockTransferItem> {
  return apiFetch<StockTransferItem>(`/api/v1/inventory/transfers/${transferId}/ship`, { method: 'POST' });
}

export async function receiveTransfer(transferId: string): Promise<StockTransferItem> {
  return apiFetch<StockTransferItem>(`/api/v1/inventory/transfers/${transferId}/receive`, { method: 'POST' });
}

export async function cancelTransfer(transferId: string): Promise<StockTransferItem> {
  return apiFetch<StockTransferItem>(`/api/v1/inventory/transfers/${transferId}/cancel`, { method: 'POST' });
}

export async function addTransferItem(transferId: string, data: StockTransferLineItemInput): Promise<StockTransferLineItem> {
  return apiFetch<StockTransferLineItem>(`/api/v1/inventory/transfers/${transferId}/items`, { method: 'POST', json: data });
}

export async function removeTransferItem(transferId: string, itemId: string): Promise<void> {
  await apiFetch(`/api/v1/inventory/transfers/${transferId}/items/${itemId}`, { method: 'DELETE' });
}
