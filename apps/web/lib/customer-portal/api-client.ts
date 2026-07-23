import { ApiError } from '@/lib/api-client';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const TOKEN_KEY = 'customer_access_token';
const ORG_KEY = 'customer_organization_id';

export function getCustomerToken(): string | null {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setCustomerToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearCustomerToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

export function getCustomerOrgId(): string | null {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem(ORG_KEY);
}

export function setCustomerOrgId(orgId: string): void {
  window.localStorage.setItem(ORG_KEY, orgId);
}

export function clearCustomerOrgId(): void {
  window.localStorage.removeItem(ORG_KEY);
}

const GUEST_SESSION_KEY = 'guest_session_token';

export function getOrCreateGuestSessionToken(): string {
  if (typeof window === 'undefined') return '';
  let token = window.localStorage.getItem(GUEST_SESSION_KEY);
  if (!token) {
    token = crypto.randomUUID();
    window.localStorage.setItem(GUEST_SESSION_KEY, token);
  }
  return token;
}

export function withOrg(path: string, extra: Record<string, string | undefined> = {}): string {
  const orgId = getCustomerOrgId();
  const params = new URLSearchParams();
  if (orgId) params.set('organization_id', orgId);
  Object.entries(extra).forEach(([key, value]) => {
    if (value !== undefined) params.set(key, value);
  });
  const query = params.toString();
  const separator = path.includes('?') ? '&' : '?';
  return query ? `${path}${separator}${query}` : path;
}

interface PortalFetchOptions extends RequestInit {
  auth?: boolean;
  json?: unknown;
}

export async function portalApiFetch<T>(path: string, options: PortalFetchOptions = {}): Promise<T> {
  const { auth = true, json, headers, ...rest } = options;
  const requestHeaders: Record<string, string> = {
    ...(headers as Record<string, string> | undefined),
  };

  if (json !== undefined) {
    requestHeaders['Content-Type'] = 'application/json';
  }

  if (auth) {
    const token = getCustomerToken();
    if (token) {
      requestHeaders.Authorization = `Bearer ${token}`;
    }
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: requestHeaders,
    body: json !== undefined ? JSON.stringify(json) : rest.body,
    credentials: 'include',
    cache: 'no-store',
  });

  if (!response.ok) {
    let detail: unknown = null;
    try {
      const data = await response.json();
      detail = data.detail ?? data;
    } catch {
      detail = response.statusText;
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return (await response.json()) as T;
  }
  return (await response.text()) as unknown as T;
}
