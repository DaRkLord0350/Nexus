import { API_BASE } from '@/lib/api-client';
import { NotificationItem, NotificationListResponse, NotificationPreferenceItem, UnreadCountResponse } from '@/lib/types';

const NOTIFICATION_CHANNELS = ['in_app', 'email', 'database', 'sms'] as const;
export type NotificationChannel = (typeof NOTIFICATION_CHANNELS)[number];

function getAuthHeaders(token?: string | null) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

async function buildUrl(path: string): Promise<string> {
  if (API_BASE) {
    return `${API_BASE}${path}`;
  }
  return path;
}

export async function getNotifications(token?: string | null): Promise<NotificationItem[]> {
  const url = await buildUrl('/api/v1/notifications');
  const response = await fetch(url, {
    headers: getAuthHeaders(token),
    cache: 'no-store',
  });
  if (!response.ok) {
    throw new Error('Unable to load notifications.');
  }
  const data = (await response.json()) as NotificationListResponse;
  return data.notifications;
}

export async function getUnreadCount(token?: string | null): Promise<number> {
  const url = await buildUrl('/api/v1/notifications/unread-count');
  const response = await fetch(url, {
    headers: getAuthHeaders(token),
    cache: 'no-store',
  });
  if (!response.ok) {
    throw new Error('Unable to load unread count.');
  }
  const data = (await response.json()) as UnreadCountResponse;
  return data.unread_count;
}

export async function markNotificationRead(notificationId: string, token?: string | null) {
  const url = await buildUrl(`/api/v1/notifications/${notificationId}/read`);
  const response = await fetch(url, {
    method: 'POST',
    headers: getAuthHeaders(token),
  });
  if (!response.ok) {
    throw new Error('Unable to mark notification as read.');
  }
}

export async function markAllNotificationsRead(token?: string | null) {
  const url = await buildUrl('/api/v1/notifications/read-all');
  const response = await fetch(url, {
    method: 'POST',
    headers: getAuthHeaders(token),
  });
  if (!response.ok) {
    throw new Error('Unable to mark all notifications as read.');
  }
}

export async function getNotificationPreferences(token?: string | null): Promise<NotificationPreferenceItem[]> {
  const url = await buildUrl('/api/v1/notifications/preferences');
  const response = await fetch(url, { headers: getAuthHeaders(token), cache: 'no-store' });
  if (!response.ok) {
    throw new Error('Unable to load notification preferences.');
  }
  return (await response.json()) as NotificationPreferenceItem[];
}

export async function updateNotificationPreference(
  channel: NotificationChannel,
  enabled: boolean,
  token?: string | null,
): Promise<NotificationPreferenceItem> {
  const url = await buildUrl('/api/v1/notifications/preferences');
  const response = await fetch(url, {
    method: 'PATCH',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ channel, enabled }),
  });
  if (!response.ok) {
    throw new Error('Unable to update notification preference.');
  }
  return (await response.json()) as NotificationPreferenceItem;
}

export function buildNotificationWebSocketUrl(token: string): string {
  const protocol = API_BASE.startsWith('https') ? 'wss' : 'ws';
  const host = API_BASE.replace(/^https?:/, '');
  return `${protocol}:${host}/api/v1/notifications/ws?token=${encodeURIComponent(token)}`;
}
