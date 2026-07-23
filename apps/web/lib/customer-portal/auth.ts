import { portalApiFetch, setCustomerOrgId, setCustomerToken, withOrg } from '@/lib/customer-portal/api-client';
import type { CustomerItem } from '@/lib/types';

export interface CustomerTokenResponse {
  access_token: string;
  token_type: string;
  customer: CustomerItem;
}

export async function registerCustomer(organizationId: string, data: {
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  password: string;
  accepts_marketing?: boolean;
}): Promise<CustomerTokenResponse> {
  const result = await portalApiFetch<CustomerTokenResponse>('/api/v1/customers/auth/register', {
    method: 'POST',
    json: { ...data, organization_id: organizationId },
    auth: false,
  });
  setCustomerOrgId(organizationId);
  setCustomerToken(result.access_token);
  return result;
}

export async function loginCustomer(organizationId: string, email: string, password: string): Promise<CustomerTokenResponse> {
  const result = await portalApiFetch<CustomerTokenResponse>('/api/v1/customers/auth/login', {
    method: 'POST',
    json: { email, password, organization_id: organizationId },
    auth: false,
  });
  setCustomerOrgId(organizationId);
  setCustomerToken(result.access_token);
  return result;
}

export async function fetchMyProfile(): Promise<CustomerItem> {
  return portalApiFetch<CustomerItem>(withOrg('/api/v1/customers/auth/me'));
}
