import { apiFetch } from '@/lib/api-client';
import type { CourierPerformanceResponse } from '@/lib/types';

export async function fetchCourierPerformance(dateFrom?: string, dateTo?: string): Promise<CourierPerformanceResponse> {
  const params = new URLSearchParams();
  if (dateFrom) params.set('date_from', dateFrom);
  if (dateTo) params.set('date_to', dateTo);
  const query = params.toString();
  return apiFetch<CourierPerformanceResponse>(`/api/v1/shipping/analytics/courier-performance${query ? `?${query}` : ''}`);
}
