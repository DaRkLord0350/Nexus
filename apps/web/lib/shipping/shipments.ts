import { apiFetch } from '@/lib/api-client';
import type { ShipmentDetail, ShipmentListResponse, ShipmentRead, ShipmentTrackingEventRead } from '@/lib/types';

export interface ShipmentFilters {
  orderId?: string;
  warehouseId?: string;
  shippingProviderId?: string;
  status?: string;
  q?: string;
  limit?: number;
  offset?: number;
}

export interface ShipmentItemInput {
  order_item_id: string;
  quantity: number;
}

export interface ShipmentCreateInput {
  order_id: string;
  warehouse_id?: string;
  shipping_provider_id?: string;
  items: ShipmentItemInput[];
  weight?: number;
  shipping_cost?: number;
  is_cod?: boolean;
  cod_amount?: number;
  service_type?: string;
  notes?: string;
}

function buildQuery(filters: ShipmentFilters): string {
  const params = new URLSearchParams();
  if (filters.orderId) params.set('order_id', filters.orderId);
  if (filters.warehouseId) params.set('warehouse_id', filters.warehouseId);
  if (filters.shippingProviderId) params.set('shipping_provider_id', filters.shippingProviderId);
  if (filters.status) params.set('status', filters.status);
  if (filters.q) params.set('q', filters.q);
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchShipments(filters: ShipmentFilters = {}): Promise<ShipmentListResponse> {
  return apiFetch<ShipmentListResponse>(`/api/v1/shipping/shipments/?${buildQuery(filters)}`);
}

export async function fetchShipment(shipmentId: string): Promise<ShipmentDetail> {
  return apiFetch<ShipmentDetail>(`/api/v1/shipping/shipments/${shipmentId}`);
}

export async function createShipment(data: ShipmentCreateInput): Promise<ShipmentDetail> {
  return apiFetch<ShipmentDetail>('/api/v1/shipping/shipments/', { method: 'POST', json: data });
}

const WORKFLOW_ACTIONS = ['label', 'pickup', 'in-transit', 'out-for-delivery', 'deliver', 'return'] as const;
export type ShipmentWorkflowAction = (typeof WORKFLOW_ACTIONS)[number];

export async function applyShipmentTransition(shipmentId: string, action: ShipmentWorkflowAction): Promise<ShipmentRead> {
  return apiFetch<ShipmentRead>(`/api/v1/shipping/shipments/${shipmentId}/${action}`, { method: 'POST' });
}

export async function failShipmentDelivery(shipmentId: string, reason?: string): Promise<ShipmentRead> {
  return apiFetch<ShipmentRead>(`/api/v1/shipping/shipments/${shipmentId}/fail-delivery`, { method: 'POST', json: { reason } });
}

export async function cancelShipment(shipmentId: string, reason?: string): Promise<ShipmentRead> {
  return apiFetch<ShipmentRead>(`/api/v1/shipping/shipments/${shipmentId}/cancel`, { method: 'POST', json: { reason } });
}

export async function fetchShipmentTracking(shipmentId: string): Promise<ShipmentTrackingEventRead[]> {
  return apiFetch<ShipmentTrackingEventRead[]>(`/api/v1/shipping/shipments/${shipmentId}/tracking`);
}

export async function addShipmentTrackingEvent(shipmentId: string, status: string, description?: string, location?: string): Promise<ShipmentTrackingEventRead> {
  return apiFetch<ShipmentTrackingEventRead>(`/api/v1/shipping/shipments/${shipmentId}/tracking`, { method: 'POST', json: { status, description, location } });
}

export async function fetchShipmentLabelHtml(shipmentId: string): Promise<string> {
  return apiFetch<string>(`/api/v1/shipping/shipments/${shipmentId}/label`);
}

export async function fetchShipmentPackingSlipHtml(shipmentId: string): Promise<string> {
  return apiFetch<string>(`/api/v1/shipping/shipments/${shipmentId}/packing-slip`);
}

export async function fetchBulkLabelsHtml(shipmentIds: string[]): Promise<string> {
  return apiFetch<string>('/api/v1/shipping/shipments/bulk-labels', { method: 'POST', json: { shipment_ids: shipmentIds } });
}

export async function generateManifestHtml(warehouseId: string, shipmentIds: string[]): Promise<string> {
  return apiFetch<string>('/api/v1/shipping/shipments/manifests', { method: 'POST', json: { warehouse_id: warehouseId, shipment_ids: shipmentIds } });
}
