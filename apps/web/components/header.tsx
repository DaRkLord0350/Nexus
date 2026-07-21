'use client';

import { LogOut } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '@/components/auth-provider';
import { NotificationDropdown } from '@/components/notification-dropdown';
import { ThemeToggle } from '@/components/theme-toggle';

export function Header() {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  const initials = user ? `${user.first_name?.[0] ?? ''}${user.last_name?.[0] ?? ''}`.toUpperCase() : '';

  return (
    <header className="border-b border-slate-200 bg-white/90 py-4 px-6 shadow-sm backdrop-blur-xl dark:border-slate-800 dark:bg-slate-900/90">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-cyan-600 dark:text-cyan-300">CommerceOS</p>
          <h1 className="text-xl font-semibold text-slate-900 dark:text-white">Dashboard</h1>
        </div>
        <div className="flex items-center gap-3">
          <ThemeToggle />
          <NotificationDropdown />
          <div className="relative">
            <button
              type="button"
              onClick={() => setMenuOpen((v) => !v)}
              className="flex h-9 w-9 items-center justify-center rounded-full bg-cyan-500 text-sm font-semibold text-slate-950"
            >
              {initials || '?'}
            </button>
            {menuOpen ? (
              <div className="absolute right-0 z-50 mt-2 w-56 rounded-2xl border border-slate-200 bg-white p-2 shadow-xl dark:border-slate-800 dark:bg-slate-900">
                <div className="px-3 py-2">
                  <p className="truncate text-sm font-semibold text-slate-900 dark:text-white">
                    {user ? `${user.first_name} ${user.last_name}` : ''}
                  </p>
                  <p className="truncate text-xs text-slate-500 dark:text-slate-400">{user?.email}</p>
                </div>
                <a
                  href="/dashboard/profile"
                  className="block rounded-xl px-3 py-2 text-sm text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                >
                  Profile
                </a>
                <button
                  type="button"
                  onClick={() => logout()}
                  className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10"
                >
                  <LogOut size={14} />
                  Sign out
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </header>
  );
}
