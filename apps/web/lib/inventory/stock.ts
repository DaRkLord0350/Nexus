import { apiFetch } from '@/lib/api-client';
import type {
  InventoryItem,
  InventoryListResponse,
  InventoryTransactionListResponse,
} from '@/lib/types';

export interface InventoryFilters {
  warehouseId?: string;
  productId?: string;
  lowStockOnly?: boolean;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface InventoryUpdateInput {
  bin_id?: string;
  minimum_stock?: number;
  maximum_stock?: number;
  reorder_point?: number;
}

function buildQuery(filters: InventoryFilters): string {
  const params = new URLSearchParams();
  if (filters.warehouseId) params.set('warehouse_id', filters.warehouseId);
  if (filters.productId) params.set('product_id', filters.productId);
  if (filters.lowStockOnly !== undefined) params.set('low_stock_only', String(filters.lowStockOnly));
  params.set('sort_by', filters.sortBy ?? 'updated_at');
  params.set('sort_order', filters.sortOrder ?? 'desc');
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchInventory(filters: InventoryFilters = {}): Promise<InventoryListResponse> {
  return apiFetch<InventoryListResponse>(`/api/v1/inventory/stock/?${buildQuery(filters)}`);
}

export async function fetchInventoryRecord(inventoryId: string): Promise<InventoryItem> {
  return apiFetch<InventoryItem>(`/api/v1/inventory/stock/${inventoryId}`);
}

export async function updateInventoryRecord(inventoryId: string, data: InventoryUpdateInput): Promise<InventoryItem> {
  return apiFetch<InventoryItem>(`/api/v1/inventory/stock/${inventoryId}`, { method: 'PATCH', json: data });
}

export interface InventoryTransactionFilters {
  inventoryId?: string;
  warehouseId?: string;
  productId?: string;
  type?: string;
  limit?: number;
  offset?: number;
}

function buildTransactionQuery(filters: InventoryTransactionFilters): string {
  const params = new URLSearchParams();
  if (filters.inventoryId) params.set('inventory_id', filters.inventoryId);
  if (filters.warehouseId) params.set('warehouse_id', filters.warehouseId);
  if (filters.productId) params.set('product_id', filters.productId);
  if (filters.type) params.set('type', filters.type);
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchInventoryTransactions(filters: InventoryTransactionFilters = {}): Promise<InventoryTransactionListResponse> {
  return apiFetch<InventoryTransactionListResponse>(`/api/v1/inventory/stock/transactions?${buildTransactionQuery(filters)}`);
}
