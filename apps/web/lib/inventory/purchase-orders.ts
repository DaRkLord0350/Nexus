import { apiFetch } from '@/lib/api-client';
import type { PurchaseOrderDetail, PurchaseOrderItem, PurchaseOrderLineItem, PurchaseOrderListResponse } from '@/lib/types';

export interface PurchaseOrderFilters {
  warehouseId?: string;
  status?: string;
  q?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface PurchaseOrderLineItemInput {
  product_id: string;
  variant_id?: string;
  quantity_ordered: number;
  unit_cost?: number;
  tax_rate?: number;
  notes?: string;
}

export interface PurchaseOrderCreateInput {
  po_number?: string;
  supplier_name: string;
  supplier_email?: string;
  supplier_phone?: string;
  warehouse_id: string;
  currency?: string;
  tax_amount?: number;
  shipping_amount?: number;
  expected_date?: string;
  notes?: string;
  items?: PurchaseOrderLineItemInput[];
}

export interface PurchaseOrderUpdateInput {
  supplier_name?: string;
  supplier_email?: string;
  supplier_phone?: string;
  currency?: string;
  tax_amount?: number;
  shipping_amount?: number;
  expected_date?: string;
  notes?: string;
}

function buildQuery(filters: PurchaseOrderFilters): string {
  const params = new URLSearchParams();
  if (filters.warehouseId) params.set('warehouse_id', filters.warehouseId);
  if (filters.status) params.set('status', filters.status);
  if (filters.q) params.set('q', filters.q);
  params.set('sort_by', filters.sortBy ?? 'created_at');
  params.set('sort_order', filters.sortOrder ?? 'desc');
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchPurchaseOrders(filters: PurchaseOrderFilters = {}): Promise<PurchaseOrderListResponse> {
  return apiFetch<PurchaseOrderListResponse>(`/api/v1/inventory/purchase-orders/?${buildQuery(filters)}`);
}

export async function fetchPurchaseOrder(poId: string): Promise<PurchaseOrderDetail> {
  return apiFetch<PurchaseOrderDetail>(`/api/v1/inventory/purchase-orders/${poId}`);
}

export async function createPurchaseOrder(data: PurchaseOrderCreateInput): Promise<PurchaseOrderItem> {
  return apiFetch<PurchaseOrderItem>('/api/v1/inventory/purchase-orders/', { method: 'POST', json: data });
}

export async function updatePurchaseOrder(poId: string, data: PurchaseOrderUpdateInput): Promise<PurchaseOrderItem> {
  return apiFetch<PurchaseOrderItem>(`/api/v1/inventory/purchase-orders/${poId}`, { method: 'PATCH', json: data });
}

export async function deletePurchaseOrder(poId: string): Promise<void> {
  await apiFetch(`/api/v1/inventory/purchase-orders/${poId}`, { method: 'DELETE' });
}

export async function sendPurchaseOrder(poId: string): Promise<PurchaseOrderItem> {
  return apiFetch<PurchaseOrderItem>(`/api/v1/inventory/purchase-orders/${poId}/send`, { method: 'POST' });
}

export async function cancelPurchaseOrder(poId: string): Promise<PurchaseOrderItem> {
  return apiFetch<PurchaseOrderItem>(`/api/v1/inventory/purchase-orders/${poId}/cancel`, { method: 'POST' });
}

export async function addPurchaseOrderItem(poId: string, data: PurchaseOrderLineItemInput): Promise<PurchaseOrderLineItem> {
  return apiFetch<PurchaseOrderLineItem>(`/api/v1/inventory/purchase-orders/${poId}/items`, { method: 'POST', json: data });
}

export async function removePurchaseOrderItem(poId: string, itemId: string): Promise<void> {
  await apiFetch(`/api/v1/inventory/purchase-orders/${poId}/items/${itemId}`, { method: 'DELETE' });
}
