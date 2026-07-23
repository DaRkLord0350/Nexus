import { portalApiFetch, withOrg } from '@/lib/customer-portal/api-client';
import type { ReturnRequestDetail, ReturnRequestListResponse } from '@/lib/types';

export interface MyReturnItemInput {
  order_item_id: string;
  quantity: number;
  reason_code?: string;
}

export interface MyReturnCreateInput {
  order_id: string;
  reason_code: string;
  reason_notes?: string;
  items: MyReturnItemInput[];
}

export async function fetchMyReturns(status?: string, limit = 20, offset = 0): Promise<ReturnRequestListResponse> {
  return portalApiFetch<ReturnRequestListResponse>(withOrg('/api/v1/customers/me/returns', { status, limit: String(limit), offset: String(offset) }));
}

export async function fetchMyReturn(returnId: string): Promise<ReturnRequestDetail> {
  return portalApiFetch<ReturnRequestDetail>(withOrg(`/api/v1/customers/me/returns/${returnId}`));
}

export async function createMyReturn(data: MyReturnCreateInput): Promise<ReturnRequestDetail> {
  return portalApiFetch<ReturnRequestDetail>(withOrg('/api/v1/customers/me/returns'), { method: 'POST', json: data });
}
