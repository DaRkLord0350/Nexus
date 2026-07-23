import { portalApiFetch, withOrg } from '@/lib/customer-portal/api-client';
import type { AddressListResponse, AddressItem, AddressType } from '@/lib/types';

export interface MyAddressInput {
  label?: string;
  address_type?: AddressType;
  first_name: string;
  last_name: string;
  company?: string;
  phone?: string;
  line1: string;
  line2?: string;
  city: string;
  state?: string;
  postal_code?: string;
  country: string;
  is_default?: boolean;
}

export async function fetchMyAddresses(): Promise<AddressListResponse> {
  return portalApiFetch<AddressListResponse>(withOrg('/api/v1/customers/me/addresses'));
}

export async function addMyAddress(data: MyAddressInput): Promise<AddressItem> {
  return portalApiFetch<AddressItem>(withOrg('/api/v1/customers/me/addresses'), { method: 'POST', json: data });
}

export async function deleteMyAddress(addressId: string): Promise<void> {
  await portalApiFetch(withOrg(`/api/v1/customers/me/addresses/${addressId}`), { method: 'DELETE' });
}
