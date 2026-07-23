import { apiFetch } from '@/lib/api-client';
import type { ReturnShipmentListResponse, ReturnShipmentRead } from '@/lib/types';

export async function fetchReturnShipments(warehouseId?: string, status?: string, limit = 50, offset = 0): Promise<ReturnShipmentListResponse> {
  const params = new URLSearchParams();
  if (warehouseId) params.set('warehouse_id', warehouseId);
  if (status) params.set('status', status);
  params.set('limit', String(limit));
  params.set('offset', String(offset));
  return apiFetch<ReturnShipmentListResponse>(`/api/v1/shipping/return-shipments/?${params.toString()}`);
}

export async function fetchReturnShipment(id: string): Promise<ReturnShipmentRead> {
  return apiFetch<ReturnShipmentRead>(`/api/v1/shipping/return-shipments/${id}`);
}

export async function createReturnShipment(returnRequestId: string, warehouseId: string, shippingProviderId?: string): Promise<ReturnShipmentRead> {
  return apiFetch<ReturnShipmentRead>('/api/v1/shipping/return-shipments/', {
    method: 'POST',
    json: { return_request_id: returnRequestId, warehouse_id: warehouseId, shipping_provider_id: shippingProviderId },
  });
}

export async function generateReturnLabel(id: string): Promise<ReturnShipmentRead> {
  return apiFetch<ReturnShipmentRead>(`/api/v1/shipping/return-shipments/${id}/label`, { method: 'POST' });
}

export async function scheduleReversePickup(id: string, scheduledAt: string): Promise<ReturnShipmentRead> {
  return apiFetch<ReturnShipmentRead>(`/api/v1/shipping/return-shipments/${id}/schedule-pickup`, { method: 'POST', json: { scheduled_at: scheduledAt } });
}

export async function markReturnShipmentInTransit(id: string): Promise<ReturnShipmentRead> {
  return apiFetch<ReturnShipmentRead>(`/api/v1/shipping/return-shipments/${id}/in-transit`, { method: 'POST' });
}

export async function markReturnShipmentReceived(id: string): Promise<ReturnShipmentRead> {
  return apiFetch<ReturnShipmentRead>(`/api/v1/shipping/return-shipments/${id}/receive`, { method: 'POST' });
}

export async function cancelReturnShipment(id: string, reason?: string): Promise<ReturnShipmentRead> {
  return apiFetch<ReturnShipmentRead>(`/api/v1/shipping/return-shipments/${id}/cancel`, { method: 'POST', json: { reason } });
}
