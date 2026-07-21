const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const ACCESS_TOKEN_KEY = 'access_token';

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === 'string' ? detail : (detail as { message?: string })?.message || `Request failed with status ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
}

interface ApiFetchOptions extends RequestInit {
  auth?: boolean;
  json?: unknown;
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { auth = true, json, headers, ...rest } = options;
  const requestHeaders: Record<string, string> = {
    ...(headers as Record<string, string> | undefined),
  };

  if (json !== undefined) {
    requestHeaders['Content-Type'] = 'application/json';
  }

  if (auth) {
    const token = getAccessToken();
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

export { API_BASE };
