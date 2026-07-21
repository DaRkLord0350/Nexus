import { apiFetch } from '@/lib/api-client';
import type { Role } from '@/lib/types';

export async function listRoles(): Promise<Role[]> {
  return apiFetch<Role[]>('/api/v1/rbac/roles');
}

export async function createRole(name: string, description: string, permissionCodes: string[]): Promise<Role> {
  return apiFetch<Role>('/api/v1/rbac/roles', {
    method: 'POST',
    json: { name, description, permission_codes: permissionCodes },
  });
}

export async function assignRole(roleId: string, userId: string): Promise<void> {
  await apiFetch(`/api/v1/rbac/roles/${roleId}/assign`, { method: 'POST', json: { user_id: userId } });
}

export async function removeRole(roleId: string, userId: string): Promise<void> {
  await apiFetch(`/api/v1/rbac/roles/${roleId}/assignments`, { method: 'DELETE', json: { user_id: userId } });
}
