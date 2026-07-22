import { apiFetch } from '@/lib/api-client';
import type {
  WarehouseBinItem,
  WarehouseBinListResponse,
  WarehouseItem,
  WarehouseListResponse,
  WarehouseZoneItem,
  WarehouseZoneListResponse,
} from '@/lib/types';

export interface WarehouseFilters {
  type?: string;
  isActive?: boolean;
  q?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface WarehouseCreateInput {
  name: string;
  code: string;
  warehouse_type?: string;
  email?: string;
  phone?: string;
  country?: string;
  state?: string;
  city?: string;
  zipcode?: string;
  address?: string;
  is_default?: boolean;
  is_active?: boolean;
}

export type WarehouseUpdateInput = Partial<WarehouseCreateInput>;

function buildQuery(filters: WarehouseFilters): string {
  const params = new URLSearchParams();
  if (filters.type) params.set('type', filters.type);
  if (filters.isActive !== undefined) params.set('is_active', String(filters.isActive));
  if (filters.q) params.set('q', filters.q);
  params.set('sort_by', filters.sortBy ?? 'name');
  params.set('sort_order', filters.sortOrder ?? 'asc');
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchWarehouses(filters: WarehouseFilters = {}): Promise<WarehouseListResponse> {
  return apiFetch<WarehouseListResponse>(`/api/v1/inventory/warehouses/?${buildQuery(filters)}`);
}

export async function fetchWarehouse(warehouseId: string): Promise<WarehouseItem> {
  return apiFetch<WarehouseItem>(`/api/v1/inventory/warehouses/${warehouseId}`);
}

export async function createWarehouse(data: WarehouseCreateInput): Promise<WarehouseItem> {
  return apiFetch<WarehouseItem>('/api/v1/inventory/warehouses/', { method: 'POST', json: data });
}

export async function updateWarehouse(warehouseId: string, data: WarehouseUpdateInput): Promise<WarehouseItem> {
  return apiFetch<WarehouseItem>(`/api/v1/inventory/warehouses/${warehouseId}`, { method: 'PATCH', json: data });
}

export async function deleteWarehouse(warehouseId: string): Promise<void> {
  await apiFetch(`/api/v1/inventory/warehouses/${warehouseId}`, { method: 'DELETE' });
}

export async function bulkDeleteWarehouses(ids: string[]): Promise<{ deleted_count: number }> {
  return apiFetch(`/api/v1/inventory/warehouses/bulk-delete`, { method: 'POST', json: { ids } });
}

export async function restoreWarehouse(warehouseId: string): Promise<WarehouseItem> {
  return apiFetch<WarehouseItem>(`/api/v1/inventory/warehouses/${warehouseId}/restore`, { method: 'POST' });
}

export async function setDefaultWarehouse(warehouseId: string): Promise<WarehouseItem> {
  return apiFetch<WarehouseItem>(`/api/v1/inventory/warehouses/${warehouseId}/default`, { method: 'POST' });
}

export interface WarehouseZoneCreateInput {
  name: string;
  code: string;
  zone_type?: string;
  description?: string;
  is_active?: boolean;
}

export type WarehouseZoneUpdateInput = Partial<WarehouseZoneCreateInput>;

export async function fetchZones(warehouseId: string): Promise<WarehouseZoneListResponse> {
  return apiFetch<WarehouseZoneListResponse>(`/api/v1/inventory/warehouses/${warehouseId}/zones?limit=200`);
}

export async function createZone(warehouseId: string, data: WarehouseZoneCreateInput): Promise<WarehouseZoneItem> {
  return apiFetch<WarehouseZoneItem>(`/api/v1/inventory/warehouses/${warehouseId}/zones`, { method: 'POST', json: data });
}

export async function updateZone(warehouseId: string, zoneId: string, data: WarehouseZoneUpdateInput): Promise<WarehouseZoneItem> {
  return apiFetch<WarehouseZoneItem>(`/api/v1/inventory/warehouses/${warehouseId}/zones/${zoneId}`, { method: 'PATCH', json: data });
}

export async function deleteZone(warehouseId: string, zoneId: string): Promise<void> {
  await apiFetch(`/api/v1/inventory/warehouses/${warehouseId}/zones/${zoneId}`, { method: 'DELETE' });
}

export interface WarehouseBinCreateInput {
  zone_id?: string;
  code: string;
  aisle?: string;
  rack?: string;
  shelf?: string;
  bin_number?: string;
  capacity?: number;
  status?: string;
}

export type WarehouseBinUpdateInput = Partial<WarehouseBinCreateInput>;

export async function fetchBins(warehouseId: string, zoneId?: string): Promise<WarehouseBinListResponse> {
  const params = new URLSearchParams({ limit: '200' });
  if (zoneId) params.set('zone_id', zoneId);
  return apiFetch<WarehouseBinListResponse>(`/api/v1/inventory/warehouses/${warehouseId}/bins?${params.toString()}`);
}

export async function createBin(warehouseId: string, data: WarehouseBinCreateInput): Promise<WarehouseBinItem> {
  return apiFetch<WarehouseBinItem>(`/api/v1/inventory/warehouses/${warehouseId}/bins`, { method: 'POST', json: data });
}

export async function updateBin(warehouseId: string, binId: string, data: WarehouseBinUpdateInput): Promise<WarehouseBinItem> {
  return apiFetch<WarehouseBinItem>(`/api/v1/inventory/warehouses/${warehouseId}/bins/${binId}`, { method: 'PATCH', json: data });
}

export async function deleteBin(warehouseId: string, binId: string): Promise<void> {
  await apiFetch(`/api/v1/inventory/warehouses/${warehouseId}/bins/${binId}`, { method: 'DELETE' });
}
