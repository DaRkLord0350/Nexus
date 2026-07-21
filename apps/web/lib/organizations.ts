import { apiFetch } from '@/lib/api-client';
import type { Organization, User } from '@/lib/types';

export async function getMyOrganization(): Promise<Organization> {
  return apiFetch<Organization>('/api/v1/organizations/me');
}

export async function updateOrganization(organizationId: string, data: Partial<Organization>): Promise<Organization> {
  return apiFetch<Organization>(`/api/v1/organizations/${organizationId}`, { method: 'PATCH', json: data });
}

export async function listMembers(organizationId: string): Promise<User[]> {
  return apiFetch<User[]>(`/api/v1/organizations/${organizationId}/members`);
}

export async function inviteMember(organizationId: string, email: string): Promise<{ detail: string; invitation_id: string }> {
  return apiFetch(`/api/v1/organizations/${organizationId}/invite`, { method: 'POST', json: { email } });
}

export async function transferOwnership(organizationId: string, newOwnerId: string): Promise<void> {
  await apiFetch(`/api/v1/organizations/${organizationId}/transfer-ownership`, { method: 'POST', json: { new_owner_id: newOwnerId } });
}

export async function deactivateOrganization(organizationId: string): Promise<Organization> {
  return apiFetch<Organization>(`/api/v1/organizations/${organizationId}/deactivate`, { method: 'POST' });
}
