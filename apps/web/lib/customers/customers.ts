import { apiFetch } from '@/lib/api-client';
import type { AddressItem, AddressListResponse, AddressType, CustomerItem, CustomerListResponse } from '@/lib/types';

export interface CustomerFilters {
  isActive?: boolean;
  isGuest?: boolean;
  q?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface CustomerCreateInput {
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  password?: string;
  accepts_marketing?: boolean;
  notes?: string;
}

export interface CustomerUpdateInput {
  first_name?: string;
  last_name?: string;
  phone?: string;
  is_active?: boolean;
  accepts_marketing?: boolean;
  notes?: string;
}

export interface AddressCreateInput {
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

function buildQuery(filters: CustomerFilters): string {
  const params = new URLSearchParams();
  if (filters.isActive !== undefined) params.set('is_active', String(filters.isActive));
  if (filters.isGuest !== undefined) params.set('is_guest', String(filters.isGuest));
  if (filters.q) params.set('q', filters.q);
  params.set('sort_by', filters.sortBy ?? 'created_at');
  params.set('sort_order', filters.sortOrder ?? 'desc');
  params.set('limit', String(filters.limit ?? 50));
  params.set('offset', String(filters.offset ?? 0));
  return params.toString();
}

export async function fetchCustomers(filters: CustomerFilters = {}): Promise<CustomerListResponse> {
  return apiFetch<CustomerListResponse>(`/api/v1/customers/?${buildQuery(filters)}`);
}

export async function fetchCustomer(customerId: string): Promise<CustomerItem> {
  return apiFetch<CustomerItem>(`/api/v1/customers/${customerId}`);
}

export async function createCustomer(data: CustomerCreateInput): Promise<CustomerItem> {
  return apiFetch<CustomerItem>('/api/v1/customers/', { method: 'POST', json: data });
}

export async function updateCustomer(customerId: string, data: CustomerUpdateInput): Promise<CustomerItem> {
  return apiFetch<CustomerItem>(`/api/v1/customers/${customerId}`, { method: 'PATCH', json: data });
}

export async function deleteCustomer(customerId: string): Promise<void> {
  await apiFetch(`/api/v1/customers/${customerId}`, { method: 'DELETE' });
}

export async function fetchCustomerAddresses(customerId: string): Promise<AddressListResponse> {
  return apiFetch<AddressListResponse>(`/api/v1/customers/${customerId}/addresses`);
}

export async function addCustomerAddress(customerId: string, data: AddressCreateInput): Promise<AddressItem> {
  return apiFetch<AddressItem>(`/api/v1/customers/${customerId}/addresses`, { method: 'POST', json: data });
}

export async function deleteCustomerAddress(customerId: string, addressId: string): Promise<void> {
  await apiFetch(`/api/v1/customers/${customerId}/addresses/${addressId}`, { method: 'DELETE' });
}
