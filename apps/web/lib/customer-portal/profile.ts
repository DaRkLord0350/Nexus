import { portalApiFetch, withOrg } from '@/lib/customer-portal/api-client';
import type { CustomerItem } from '@/lib/types';

export interface MyProfileUpdateInput {
  first_name?: string;
  last_name?: string;
  phone?: string;
  accepts_marketing?: boolean;
}

export async function fetchMyProfileDetails(): Promise<CustomerItem> {
  return portalApiFetch<CustomerItem>(withOrg('/api/v1/customers/me/'));
}

export async function updateMyProfileDetails(data: MyProfileUpdateInput): Promise<CustomerItem> {
  return portalApiFetch<CustomerItem>(withOrg('/api/v1/customers/me/'), { method: 'PATCH', json: data });
}
