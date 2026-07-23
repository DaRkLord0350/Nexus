import { apiFetch } from '@/lib/api-client';
import type { RateCompareResponse, ShippingRuleActionType, ShippingRuleConditionType, ShippingRuleListResponse, ShippingRuleRead } from '@/lib/types';

export interface ShippingRuleCreateInput {
  name: string;
  priority?: number;
  is_active?: boolean;
  condition_type: ShippingRuleConditionType;
  condition_value: string;
  action_type: ShippingRuleActionType;
  action_value: string;
}

export interface ShippingRuleUpdateInput extends Partial<ShippingRuleCreateInput> {}

export async function fetchShippingRules(limit = 100, offset = 0): Promise<ShippingRuleListResponse> {
  return apiFetch<ShippingRuleListResponse>(`/api/v1/shipping/rules/?limit=${limit}&offset=${offset}`);
}

export async function createShippingRule(data: ShippingRuleCreateInput): Promise<ShippingRuleRead> {
  return apiFetch<ShippingRuleRead>('/api/v1/shipping/rules/', { method: 'POST', json: data });
}

export async function updateShippingRule(ruleId: string, data: ShippingRuleUpdateInput): Promise<ShippingRuleRead> {
  return apiFetch<ShippingRuleRead>(`/api/v1/shipping/rules/${ruleId}`, { method: 'PATCH', json: data });
}

export async function deleteShippingRule(ruleId: string): Promise<void> {
  await apiFetch(`/api/v1/shipping/rules/${ruleId}`, { method: 'DELETE' });
}

export async function compareShippingRates(destinationCountry: string, weight: number, isCod: boolean, destinationState?: string, needsInsurance = false): Promise<RateCompareResponse> {
  return apiFetch<RateCompareResponse>('/api/v1/shipping/rates/compare', {
    method: 'POST',
    json: { destination_country: destinationCountry, destination_state: destinationState, weight, is_cod: isCod, needs_insurance: needsInsurance },
  });
}
