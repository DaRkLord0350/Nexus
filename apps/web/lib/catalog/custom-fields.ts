import { apiFetch } from '@/lib/api-client';
import type { CustomFieldDefinitionListResponse, CustomFieldDefinitionItem, CustomFieldEntityType, CustomFieldValueItem } from '@/lib/types';

export interface CustomFieldDefinitionCreateInput {
  entity_type: CustomFieldEntityType;
  name: string;
  key?: string;
  field_type?: string;
  options?: string[];
  is_required?: boolean;
  sort_order?: number;
  is_active?: boolean;
}

export type CustomFieldDefinitionUpdateInput = Partial<Omit<CustomFieldDefinitionCreateInput, 'entity_type' | 'key'>>;

export async function fetchCustomFieldDefinitions(entityType: CustomFieldEntityType): Promise<CustomFieldDefinitionListResponse> {
  return apiFetch<CustomFieldDefinitionListResponse>(`/api/v1/catalog/custom-fields/definitions?entity_type=${entityType}`);
}

export async function createCustomFieldDefinition(data: CustomFieldDefinitionCreateInput): Promise<CustomFieldDefinitionItem> {
  return apiFetch<CustomFieldDefinitionItem>('/api/v1/catalog/custom-fields/definitions', { method: 'POST', json: data });
}

export async function updateCustomFieldDefinition(id: string, data: CustomFieldDefinitionUpdateInput): Promise<CustomFieldDefinitionItem> {
  return apiFetch<CustomFieldDefinitionItem>(`/api/v1/catalog/custom-fields/definitions/${id}`, { method: 'PATCH', json: data });
}

export async function deleteCustomFieldDefinition(id: string): Promise<void> {
  await apiFetch(`/api/v1/catalog/custom-fields/definitions/${id}`, { method: 'DELETE' });
}

export async function fetchCustomFieldValues(entityType: CustomFieldEntityType, entityId: string): Promise<CustomFieldValueItem[]> {
  return apiFetch<CustomFieldValueItem[]>(`/api/v1/catalog/custom-fields/values?entity_type=${entityType}&entity_id=${entityId}`);
}

export async function setCustomFieldValues(entityType: CustomFieldEntityType, entityId: string, values: Record<string, unknown>): Promise<CustomFieldValueItem[]> {
  return apiFetch<CustomFieldValueItem[]>(`/api/v1/catalog/custom-fields/values?entity_type=${entityType}&entity_id=${entityId}`, {
    method: 'PUT',
    json: { values },
  });
}
