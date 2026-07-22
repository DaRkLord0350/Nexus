import { apiFetch } from '@/lib/api-client';
import type { CouponItem, CouponListResponse } from '@/lib/types';

export interface CouponFilters {
  isActive?: boolean;
  q?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface CouponCreateInput {
  code: string;
  name?: string;
  description?: string;
  discount_type?: string;
  discount_value?: number;
  buy_quantity?: number;
  get_quantity?: number;
  get_discount_percentage?: number;
  min_order_amount?: number;
  max_discount_amount?: number;
  usage_limit?: number;
  usage_limit_per_customer?: number;
  starts_at?: string;
  expires_at?: string;
  is_active?: boolean;
  product_ids?: string[];
  category_ids?: string[];
  collection_ids?: string[];
}

export type CouponUpdateInput = Partial<CouponCreateInput>;

function buildQuery(filters: CouponFilters): string {
  const params = new URLSearchParams();
  if (filters.isActive !== undefined) params.set('is_active', String(filters.isActive));
  if (filters.q) params.set('q', filters.q);
  params.set('sort_by', filters.sortBy ?? 'created_at');
  params.set('sort_order', filters.sortOrder ?? 'desc');
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchCoupons(filters: CouponFilters = {}): Promise<CouponListResponse> {
  return apiFetch<CouponListResponse>(`/api/v1/catalog/coupons/?${buildQuery(filters)}`);
}

export async function createCoupon(data: CouponCreateInput): Promise<CouponItem> {
  return apiFetch<CouponItem>('/api/v1/catalog/coupons/', { method: 'POST', json: data });
}

export async function updateCoupon(couponId: string, data: CouponUpdateInput): Promise<CouponItem> {
  return apiFetch<CouponItem>(`/api/v1/catalog/coupons/${couponId}`, { method: 'PATCH', json: data });
}

export async function deleteCoupon(couponId: string): Promise<void> {
  await apiFetch(`/api/v1/catalog/coupons/${couponId}`, { method: 'DELETE' });
}

export async function bulkDeleteCoupons(ids: string[]): Promise<{ deleted_count: number }> {
  return apiFetch(`/api/v1/catalog/coupons/bulk-delete`, { method: 'POST', json: { ids } });
}
