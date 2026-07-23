import { apiFetch } from '@/lib/api-client';
import type { PickupListResponse, PickupRead } from '@/lib/types';

export interface PickupCreateInput {
  warehouse_id: string;
  shipping_provider_id?: string;
  scheduled_date: string;
  time_slot?: string;
  contact_name?: string;
  contact_phone?: string;
  notes?: string;
  shipment_ids?: string[];
}

export async function fetchPickups(warehouseId?: string, status?: string, limit = 50, offset = 0): Promise<PickupListResponse> {
  const params = new URLSearchParams();
  if (warehouseId) params.set('warehouse_id', warehouseId);
  if (status) params.set('status', status);
  params.set('limit', String(limit));
  params.set('offset', String(offset));
  return apiFetch<PickupListResponse>(`/api/v1/shipping/pickups/?${params.toString()}`);
}

export async function fetchPickup(pickupId: string): Promise<PickupRead> {
  return apiFetch<PickupRead>(`/api/v1/shipping/pickups/${pickupId}`);
}

export async function schedulePickup(data: PickupCreateInput): Promise<PickupRead> {
  return apiFetch<PickupRead>('/api/v1/shipping/pickups/', { method: 'POST', json: data });
}

export async function confirmPickup(pickupId: string): Promise<PickupRead> {
  return apiFetch<PickupRead>(`/api/v1/shipping/pickups/${pickupId}/confirm`, { method: 'POST' });
}

export async function reschedulePickup(pickupId: string, scheduledDate: string, timeSlot?: string): Promise<PickupRead> {
  return apiFetch<PickupRead>(`/api/v1/shipping/pickups/${pickupId}/reschedule`, { method: 'POST', json: { scheduled_date: scheduledDate, time_slot: timeSlot } });
}

export async function completePickup(pickupId: string): Promise<PickupRead> {
  return apiFetch<PickupRead>(`/api/v1/shipping/pickups/${pickupId}/complete`, { method: 'POST' });
}

export async function markPickupMissed(pickupId: string): Promise<PickupRead> {
  return apiFetch<PickupRead>(`/api/v1/shipping/pickups/${pickupId}/missed`, { method: 'POST' });
}

export async function cancelPickup(pickupId: string, reason?: string): Promise<PickupRead> {
  return apiFetch<PickupRead>(`/api/v1/shipping/pickups/${pickupId}/cancel`, { method: 'POST', json: { reason } });
}
