import { apiFetch, clearAccessToken, setAccessToken } from '@/lib/api-client';
import type { Permission, TokenResponse, User } from '@/lib/types';

export async function signup(input: {
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  organization_name: string;
}): Promise<User> {
  return apiFetch<User>('/api/v1/auth/signup', { method: 'POST', json: input, auth: false });
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const tokens = await apiFetch<TokenResponse>('/api/v1/auth/login', {
    method: 'POST',
    json: { email, password },
    auth: false,
  });
  setAccessToken(tokens.access_token);
  return tokens;
}

export async function logout(): Promise<void> {
  try {
    await apiFetch('/api/v1/auth/logout', { method: 'POST' });
  } finally {
    clearAccessToken();
  }
}

export async function forgotPassword(email: string): Promise<void> {
  await apiFetch('/api/v1/auth/forgot-password', { method: 'POST', json: { email }, auth: false });
}

export async function resetPassword(token: string, newPassword: string): Promise<void> {
  await apiFetch('/api/v1/auth/reset-password', { method: 'POST', json: { token, new_password: newPassword }, auth: false });
}

export async function verifyEmail(token: string): Promise<void> {
  await apiFetch('/api/v1/auth/verify-email', { method: 'POST', json: { token }, auth: false });
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  await apiFetch('/api/v1/auth/change-password', {
    method: 'POST',
    json: { current_password: currentPassword, new_password: newPassword },
  });
}

export async function getCurrentUser(): Promise<User> {
  return apiFetch<User>('/api/v1/auth/me');
}

export async function getMyPermissions(): Promise<Permission[]> {
  return apiFetch<Permission[]>('/api/v1/rbac/permissions');
}

export async function acceptInvitation(input: {
  token: string;
  first_name: string;
  last_name: string;
  password: string;
}): Promise<User> {
  return apiFetch<User>('/api/v1/organizations/invitations/accept', { method: 'POST', json: input, auth: false });
}
