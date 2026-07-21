import { apiFetch } from '@/lib/api-client';
import type { DashboardResponse } from '@/lib/types';

export async function getDashboard(): Promise<DashboardResponse> {
  return apiFetch<DashboardResponse>('/api/v1/dashboard/');
}
