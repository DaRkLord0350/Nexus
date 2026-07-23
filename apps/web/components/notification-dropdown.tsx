'use client';

import { Bell } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { getAccessToken } from '@/lib/api-client';
import { buildNotificationWebSocketUrl, getNotifications, getUnreadCount, markNotificationRead } from '@/lib/notifications';
import type { NotificationItem } from '@/lib/types';

export function NotificationDropdown() {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  // const token = getAccessToken();
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    setToken(getAccessToken());
  }, []);

  useEffect(() => {
    if (!token) return;
    getUnreadCount(token).then(setUnreadCount).catch(() => {});
  }, [token]);

  useEffect(() => {
    if (!token) return;
    const socketUrl = buildNotificationWebSocketUrl(token);
    const socket = new WebSocket(socketUrl);
    socket.addEventListener('message', (event) => {
      try {
        const message = JSON.parse(event.data) as NotificationItem;
        setNotifications((current) => [message, ...current].slice(0, 20));
        setUnreadCount((current) => current + 1);
      } catch {
        // ignore malformed payloads
      }
    });
    return () => socket.close();
  }, [token]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleOpen = async () => {
    const next = !open;
    setOpen(next);
    if (next && token) {
      try {
        const items = await getNotifications(token);
        setNotifications(items.slice(0, 10));
      } catch {
        // ignore
      }
    }
  };

  const handleMarkRead = async (id: string) => {
    if (!token) return;
    await markNotificationRead(id, token);
    setNotifications((current) => current.map((item) => (item.id === id ? { ...item, is_read: true } : item)));
    setUnreadCount((current) => Math.max(0, current - 1));
  };

  // if (!token) return null;
  if (token === null) {
  return (
    <div className="h-9 w-9" />
  );
}


  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        onClick={toggleOpen}
        aria-label="Notifications"
        className="relative flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 transition hover:border-slate-300 hover:text-slate-900 dark:border-slate-700 dark:bg-slate-950/80 dark:text-slate-300 dark:hover:border-slate-600 dark:hover:text-white"
      >
        <Bell size={16} />
        {unreadCount > 0 ? (
          <span className="absolute -right-1 -top-1 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-cyan-500 px-1 text-[10px] font-semibold text-slate-950">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        ) : null}
      </button>

      {open ? (
        <div className="absolute right-0 z-50 mt-2 w-80 rounded-2xl border border-slate-200 bg-white p-2 shadow-xl dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between px-2 py-1">
            <p className="text-sm font-semibold text-slate-900 dark:text-white">Notifications</p>
            <a href="/dashboard/notifications" className="text-xs text-cyan-600 hover:underline dark:text-cyan-300">
              View all
            </a>
          </div>
          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <p className="px-2 py-4 text-center text-sm text-slate-500 dark:text-slate-400">No notifications yet.</p>
            ) : (
              notifications.map((notification) => (
                <button
                  key={notification.id}
                  type="button"
                  onClick={() => handleMarkRead(notification.id)}
                  className={`block w-full rounded-xl px-2 py-2 text-left text-sm transition hover:bg-slate-100 dark:hover:bg-slate-800 ${
                    notification.is_read ? 'text-slate-500 dark:text-slate-400' : 'text-slate-900 dark:text-white'
                  }`}
                >
                  <p className="font-medium">{notification.title}</p>
                  <p className="truncate text-xs text-slate-500 dark:text-slate-400">{notification.message}</p>
                </button>
              ))
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
