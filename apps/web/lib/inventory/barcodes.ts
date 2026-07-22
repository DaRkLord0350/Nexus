import { apiFetch } from '@/lib/api-client';
import type { BarcodeItem, BarcodeListResponse, QRCodeItem, QRCodeListResponse } from '@/lib/types';

export interface BarcodeFilters {
  productId?: string;
  variantId?: string;
  format?: string;
  q?: string;
  limit?: number;
  offset?: number;
}

export interface BarcodeCreateInput {
  product_id?: string;
  variant_id?: string;
  value: string;
  format?: string;
  is_primary?: boolean;
}

export type BarcodeUpdateInput = Partial<Omit<BarcodeCreateInput, 'product_id' | 'variant_id'>>;

function buildQuery(filters: BarcodeFilters): string {
  const params = new URLSearchParams();
  if (filters.productId) params.set('product_id', filters.productId);
  if (filters.variantId) params.set('variant_id', filters.variantId);
  if (filters.format) params.set('format', filters.format);
  if (filters.q) params.set('q', filters.q);
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchBarcodes(filters: BarcodeFilters = {}): Promise<BarcodeListResponse> {
  return apiFetch<BarcodeListResponse>(`/api/v1/inventory/barcodes/codes?${buildQuery(filters)}`);
}

export async function createBarcode(data: BarcodeCreateInput): Promise<BarcodeItem> {
  return apiFetch<BarcodeItem>('/api/v1/inventory/barcodes/codes', { method: 'POST', json: data });
}

export async function updateBarcode(barcodeId: string, data: BarcodeUpdateInput): Promise<BarcodeItem> {
  return apiFetch<BarcodeItem>(`/api/v1/inventory/barcodes/codes/${barcodeId}`, { method: 'PATCH', json: data });
}

export async function deleteBarcode(barcodeId: string): Promise<void> {
  await apiFetch(`/api/v1/inventory/barcodes/codes/${barcodeId}`, { method: 'DELETE' });
}

export async function bulkDeleteBarcodes(ids: string[]): Promise<{ deleted_count: number }> {
  return apiFetch(`/api/v1/inventory/barcodes/codes/bulk-delete`, { method: 'POST', json: { ids } });
}

export interface QRCodeCreateInput {
  entity_type: string;
  entity_id: string;
  value: string;
  image_url?: string;
}

export type QRCodeUpdateInput = Partial<Pick<QRCodeCreateInput, 'value' | 'image_url'>>;

export async function fetchQRCodes(entityType?: string): Promise<QRCodeListResponse> {
  const params = new URLSearchParams({ limit: '200' });
  if (entityType) params.set('entity_type', entityType);
  return apiFetch<QRCodeListResponse>(`/api/v1/inventory/barcodes/qr?${params.toString()}`);
}

export async function createQRCode(data: QRCodeCreateInput): Promise<QRCodeItem> {
  return apiFetch<QRCodeItem>('/api/v1/inventory/barcodes/qr', { method: 'POST', json: data });
}

export async function updateQRCode(qrCodeId: string, data: QRCodeUpdateInput): Promise<QRCodeItem> {
  return apiFetch<QRCodeItem>(`/api/v1/inventory/barcodes/qr/${qrCodeId}`, { method: 'PATCH', json: data });
}

export async function deleteQRCode(qrCodeId: string): Promise<void> {
  await apiFetch(`/api/v1/inventory/barcodes/qr/${qrCodeId}`, { method: 'DELETE' });
}
