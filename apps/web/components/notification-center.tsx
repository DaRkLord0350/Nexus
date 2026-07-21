'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  buildNotificationWebSocketUrl,
  getNotifications,
  getUnreadCount,
  markAllNotificationsRead,
  markNotificationRead,
} from '@/lib/notifications';
import type { NotificationItem } from '@/lib/types';

function getToken(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }
  return window.localStorage.getItem('access_token');
}

export function NotificationCenter() {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMarkingAllRead, setIsMarkingAllRead] = useState(false);

  const token = useMemo(() => getToken(), []);
  const websocketUrl = useMemo(() => {
    if (!token) {
      return null;
    }
    return buildNotificationWebSocketUrl(token);
  }, [token]);

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }

    async function loadNotifications() {
      try {
        const [items, count] = await Promise.all([getNotifications(token), getUnreadCount(token)]);
        setNotifications(items);
        setUnreadCount(count);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load notifications.');
      } finally {
        setIsLoading(false);
      }
    }

    loadNotifications();
  }, [token]);

  useEffect(() => {
    if (!websocketUrl || !token) {
      return;
    }

    const socket = new WebSocket(websocketUrl);

    socket.addEventListener('message', (event) => {
      try {
        const message = JSON.parse(event.data) as NotificationItem;
        setNotifications((current) => [message, ...current].slice(0, 100));
        setUnreadCount((current) => current + 1);
      } catch {
        // Ignore malformed websocket events.
      }
    });

    socket.addEventListener('error', () => {
      setError('Notification socket encountered an error.');
    });

    return () => {
      socket.close();
    };
  }, [websocketUrl, token]);

  const handleMarkRead = async (notificationId: string) => {
    if (!token) {
      return;
    }
    try {
      await markNotificationRead(notificationId, token);
      setNotifications((current) => current.map((item) => (item.id === notificationId ? { ...item, is_read: true } : item)));
      setUnreadCount((current) => Math.max(0, current - 1));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to mark notification as read.');
    }
  };

  const handleMarkAllRead = async () => {
    if (!token) {
      return;
    }
    setIsMarkingAllRead(true);
    try {
      await markAllNotificationsRead(token);
      setNotifications((current) => current.map((item) => ({ ...item, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to mark all notifications as read.');
    } finally {
      setIsMarkingAllRead(false);
    }
  };

  if (!token) {
    return (
      <div className="rounded-3xl border border-slate-200 bg-white p-8 text-center text-slate-600 dark:border-slate-800 dark:bg-slate-900/90 dark:text-slate-300">
        <p className="text-lg font-semibold text-slate-900 dark:text-white">Sign in to access your notifications.</p>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Notifications are available after authentication is implemented.</p>
      </div>
    );
  }

  return (
    <section className="space-y-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-lg shadow-slate-200/50 dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-black/10">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-slate-500 dark:text-slate-400">Notification Center</p>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">Live updates & in-app alerts</h1>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <span className="rounded-full bg-cyan-500/10 px-3 py-1 text-sm font-medium text-cyan-600 dark:text-cyan-300">
            Unread {unreadCount}
          </span>
          <button
            type="button"
            onClick={handleMarkAllRead}
            disabled={unreadCount === 0 || isMarkingAllRead}
            className="rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-700 dark:bg-slate-950/80 dark:text-white dark:hover:border-slate-600 dark:hover:bg-slate-900"
          >
            Mark all read
          </button>
        </div>
      </div>

      {error ? (
        <div className="rounded-3xl border border-red-300 bg-red-50 p-4 text-sm text-red-700 dark:border-red-500/20 dark:bg-red-500/5 dark:text-red-200">{error}</div>
      ) : null}

      {isLoading ? (
        <div className="rounded-3xl border border-slate-200 bg-slate-50 p-8 text-center text-slate-500 dark:border-slate-800 dark:bg-slate-950/80 dark:text-slate-400">Loading notifications...</div>
      ) : notifications.length === 0 ? (
        <div className="rounded-3xl border border-slate-200 bg-slate-50 p-8 text-center text-slate-500 dark:border-slate-800 dark:bg-slate-950/80 dark:text-slate-400">No notifications yet.</div>
      ) : (
        <div className="space-y-4">
          {notifications.map((notification) => (
            <article
              key={notification.id}
              className={`rounded-3xl border p-5 shadow-sm transition ${notification.is_read ? 'border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-950/80' : 'border-cyan-500/30 bg-cyan-50/50 dark:border-cyan-500/20 dark:bg-slate-900/90'}`}
            >
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-600 dark:text-cyan-400">{notification.type}</p>
                  <h2 className="mt-2 text-lg font-semibold text-slate-900 dark:text-white">{notification.title}</h2>
                  <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{notification.message}</p>
                </div>
                <div className="flex flex-col items-start gap-2 text-right sm:items-end">
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs uppercase tracking-[0.24em] text-slate-600 dark:bg-slate-950/80 dark:text-slate-300">
                    {notification.channel.replace('_', ' ')}
                  </span>
                  <span className="text-xs text-slate-400 dark:text-slate-500">{new Date(notification.created_at).toLocaleString()}</span>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-3">
                {!notification.is_read ? (
                  <button
                    type="button"
                    onClick={() => handleMarkRead(notification.id)}
                    className="rounded-full bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400"
                  >
                    Mark read
                  </button>
                ) : (
                  <span className="text-xs uppercase tracking-[0.24em] text-slate-400 dark:text-slate-500">Read</span>
                )}
                {notification.metadata ? (
                  <span className="text-xs text-slate-400 dark:text-slate-500">
                    {Object.entries(notification.metadata).map(([key, value]) => `${key}: ${String(value)}`).join(' • ')}
                  </span>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
