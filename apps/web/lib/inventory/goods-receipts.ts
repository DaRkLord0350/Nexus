import { apiFetch } from '@/lib/api-client';
import type { GoodsReceiptDetail, GoodsReceiptItem, GoodsReceiptLineItem, GoodsReceiptListResponse } from '@/lib/types';

export interface GoodsReceiptFilters {
  warehouseId?: string;
  purchaseOrderId?: string;
  status?: string;
  q?: string;
  limit?: number;
  offset?: number;
}

export interface GoodsReceiptLineItemInput {
  purchase_order_item_id?: string;
  product_id: string;
  variant_id?: string;
  quantity_received: number;
  unit_cost?: number;
  batch_number?: string;
  expiry_date?: string;
  manufactured_date?: string;
  bin_id?: string;
  notes?: string;
}

export interface GoodsReceiptCreateInput {
  receipt_number?: string;
  purchase_order_id?: string;
  warehouse_id: string;
  received_date?: string;
  notes?: string;
  items?: GoodsReceiptLineItemInput[];
}

function buildQuery(filters: GoodsReceiptFilters): string {
  const params = new URLSearchParams();
  if (filters.warehouseId) params.set('warehouse_id', filters.warehouseId);
  if (filters.purchaseOrderId) params.set('purchase_order_id', filters.purchaseOrderId);
  if (filters.status) params.set('status', filters.status);
  if (filters.q) params.set('q', filters.q);
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchGoodsReceipts(filters: GoodsReceiptFilters = {}): Promise<GoodsReceiptListResponse> {
  return apiFetch<GoodsReceiptListResponse>(`/api/v1/inventory/goods-receipts/?${buildQuery(filters)}`);
}

export async function fetchGoodsReceipt(receiptId: string): Promise<GoodsReceiptDetail> {
  return apiFetch<GoodsReceiptDetail>(`/api/v1/inventory/goods-receipts/${receiptId}`);
}

export async function createGoodsReceipt(data: GoodsReceiptCreateInput): Promise<GoodsReceiptItem> {
  return apiFetch<GoodsReceiptItem>('/api/v1/inventory/goods-receipts/', { method: 'POST', json: data });
}

export async function completeGoodsReceipt(receiptId: string): Promise<GoodsReceiptItem> {
  return apiFetch<GoodsReceiptItem>(`/api/v1/inventory/goods-receipts/${receiptId}/complete`, { method: 'POST' });
}

export async function cancelGoodsReceipt(receiptId: string): Promise<GoodsReceiptItem> {
  return apiFetch<GoodsReceiptItem>(`/api/v1/inventory/goods-receipts/${receiptId}/cancel`, { method: 'POST' });
}

export async function addGoodsReceiptItem(receiptId: string, data: GoodsReceiptLineItemInput): Promise<GoodsReceiptLineItem> {
  return apiFetch<GoodsReceiptLineItem>(`/api/v1/inventory/goods-receipts/${receiptId}/items`, { method: 'POST', json: data });
}

export async function removeGoodsReceiptItem(receiptId: string, itemId: string): Promise<void> {
  await apiFetch(`/api/v1/inventory/goods-receipts/${receiptId}/items/${itemId}`, { method: 'DELETE' });
}
