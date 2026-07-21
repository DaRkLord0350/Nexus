import { apiFetch, getAccessToken, API_BASE } from '@/lib/api-client';
import type { AuditLogListResponse } from '@/lib/types';

export interface AuditFilters {
  module?: string;
  action?: string;
  entity?: string;
  userId?: string;
  dateFrom?: string;
  dateTo?: string;
  q?: string;
  limit?: number;
  offset?: number;
}

function buildQuery(filters: AuditFilters): string {
  const params = new URLSearchParams();
  if (filters.module) params.set('module', filters.module);
  if (filters.action) params.set('action', filters.action);
  if (filters.entity) params.set('entity', filters.entity);
  if (filters.userId) params.set('user_id', filters.userId);
  if (filters.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters.dateTo) params.set('date_to', filters.dateTo);
  if (filters.q) params.set('q', filters.q);
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchAuditLogs(filters: AuditFilters): Promise<AuditLogListResponse> {
  return apiFetch<AuditLogListResponse>(`/api/v1/audit/search?${buildQuery(filters)}`);
}

export function buildExportUrl(filters: AuditFilters): string {
  const params = new URLSearchParams();
  if (filters.module) params.set('module', filters.module);
  if (filters.action) params.set('action', filters.action);
  if (filters.entity) params.set('entity', filters.entity);
  if (filters.userId) params.set('user_id', filters.userId);
  if (filters.dateFrom) params.set('date_from', filters.dateFrom);
  if (filters.dateTo) params.set('date_to', filters.dateTo);
  if (filters.q) params.set('q', filters.q);
  return `${API_BASE}/api/v1/audit/export?${params.toString()}`;
}

export async function downloadAuditExport(filters: AuditFilters): Promise<void> {
  const token = getAccessToken();
  const response = await fetch(buildExportUrl(filters), {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!response.ok) {
    throw new Error('Unable to export audit logs.');
  }
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'audit-log-export.csv';
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
