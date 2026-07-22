import { apiFetch } from '@/lib/api-client';
import type { SerialNumberItem, SerialNumberListResponse } from '@/lib/types';

export interface SerialNumberFilters {
  productId?: string;
  warehouseId?: string;
  batchId?: string;
  status?: string;
  q?: string;
  limit?: number;
  offset?: number;
}

export interface SerialNumberCreateInput {
  product_id: string;
  variant_id?: string;
  warehouse_id: string;
  batch_id?: string;
  bin_id?: string;
  serial: string;
  status?: string;
  notes?: string;
}

export interface SerialNumberUpdateInput {
  batch_id?: string;
  bin_id?: string;
  status?: string;
  notes?: string;
}

export interface SerialNumberImportInput {
  product_id: string;
  variant_id?: string;
  warehouse_id: string;
  batch_id?: string;
  bin_id?: string;
  serials: string[];
}

function buildQuery(filters: SerialNumberFilters): string {
  const params = new URLSearchParams();
  if (filters.productId) params.set('product_id', filters.productId);
  if (filters.warehouseId) params.set('warehouse_id', filters.warehouseId);
  if (filters.batchId) params.set('batch_id', filters.batchId);
  if (filters.status) params.set('status', filters.status);
  if (filters.q) params.set('q', filters.q);
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchSerialNumbers(filters: SerialNumberFilters = {}): Promise<SerialNumberListResponse> {
  return apiFetch<SerialNumberListResponse>(`/api/v1/inventory/serial-numbers/?${buildQuery(filters)}`);
}

export async function scanSerialNumber(serial: string): Promise<SerialNumberItem> {
  return apiFetch<SerialNumberItem>(`/api/v1/inventory/serial-numbers/scan?serial=${encodeURIComponent(serial)}`);
}

export async function createSerialNumber(data: SerialNumberCreateInput): Promise<SerialNumberItem> {
  return apiFetch<SerialNumberItem>('/api/v1/inventory/serial-numbers/', { method: 'POST', json: data });
}

export async function importSerialNumbers(data: SerialNumberImportInput): Promise<{ imported_count: number; skipped: string[] }> {
  return apiFetch('/api/v1/inventory/serial-numbers/import', { method: 'POST', json: data });
}

export async function updateSerialNumber(serialId: string, data: SerialNumberUpdateInput): Promise<SerialNumberItem> {
  return apiFetch<SerialNumberItem>(`/api/v1/inventory/serial-numbers/${serialId}`, { method: 'PATCH', json: data });
}

export async function deleteSerialNumber(serialId: string): Promise<void> {
  await apiFetch(`/api/v1/inventory/serial-numbers/${serialId}`, { method: 'DELETE' });
}

export async function bulkDeleteSerialNumbers(ids: string[]): Promise<{ deleted_count: number }> {
  return apiFetch(`/api/v1/inventory/serial-numbers/bulk-delete`, { method: 'POST', json: { ids } });
}
