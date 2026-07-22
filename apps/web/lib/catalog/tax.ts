import { apiFetch } from '@/lib/api-client';
import type { TaxClassItem, TaxClassListResponse, TaxRateItem } from '@/lib/types';

export interface TaxClassCreateInput {
  name: string;
  code?: string;
  description?: string;
  is_default?: boolean;
  is_active?: boolean;
}

export type TaxClassUpdateInput = Partial<TaxClassCreateInput>;

export interface TaxRateCreateInput {
  country: string;
  state?: string;
  rate: number;
  tax_type?: string;
  is_inclusive?: boolean;
  priority?: number;
  is_active?: boolean;
}

export type TaxRateUpdateInput = Partial<TaxRateCreateInput>;

export async function fetchTaxClasses(): Promise<TaxClassListResponse> {
  return apiFetch<TaxClassListResponse>('/api/v1/catalog/taxes/classes?limit=200');
}

export async function createTaxClass(data: TaxClassCreateInput): Promise<TaxClassItem> {
  return apiFetch<TaxClassItem>('/api/v1/catalog/taxes/classes', { method: 'POST', json: data });
}

export async function updateTaxClass(taxClassId: string, data: TaxClassUpdateInput): Promise<TaxClassItem> {
  return apiFetch<TaxClassItem>(`/api/v1/catalog/taxes/classes/${taxClassId}`, { method: 'PATCH', json: data });
}

export async function deleteTaxClass(taxClassId: string): Promise<void> {
  await apiFetch(`/api/v1/catalog/taxes/classes/${taxClassId}`, { method: 'DELETE' });
}

export async function fetchTaxRates(taxClassId: string): Promise<TaxRateItem[]> {
  return apiFetch<TaxRateItem[]>(`/api/v1/catalog/taxes/classes/${taxClassId}/rates`);
}

export async function createTaxRate(taxClassId: string, data: TaxRateCreateInput): Promise<TaxRateItem> {
  return apiFetch<TaxRateItem>(`/api/v1/catalog/taxes/classes/${taxClassId}/rates`, { method: 'POST', json: data });
}

export async function updateTaxRate(taxClassId: string, rateId: string, data: TaxRateUpdateInput): Promise<TaxRateItem> {
  return apiFetch<TaxRateItem>(`/api/v1/catalog/taxes/classes/${taxClassId}/rates/${rateId}`, { method: 'PATCH', json: data });
}

export async function deleteTaxRate(taxClassId: string, rateId: string): Promise<void> {
  await apiFetch(`/api/v1/catalog/taxes/classes/${taxClassId}/rates/${rateId}`, { method: 'DELETE' });
}
