'use client';

import {
  Bell,
  Building2,
  FolderOpen,
  LayoutDashboard,
  ScrollText,
  Settings,
  UserCircle,
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/components/auth-provider';

interface NavItem {
  href: string;
  label: string;
  icon: typeof LayoutDashboard;
  permission?: string;
}

const NAV_ITEMS: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/dashboard/files', label: 'Files', icon: FolderOpen, permission: 'files' },
  { href: '/dashboard/audit', label: 'Audit Logs', icon: ScrollText, permission: 'audit' },
  { href: '/dashboard/notifications', label: 'Notifications', icon: Bell },
  { href: '/dashboard/organization', label: 'Organization', icon: Building2 },
  { href: '/dashboard/settings', label: 'Settings', icon: Settings, permission: 'settings' },
  { href: '/dashboard/profile', label: 'Profile', icon: UserCircle },
];

export function Sidebar() {
  const pathname = usePathname();
  const { hasPermission, isLoading } = useAuth();

  const items = NAV_ITEMS.filter((item) => !item.permission || isLoading || hasPermission(item.permission));

  return (
    <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white/80 px-4 py-6 dark:border-slate-800 dark:bg-slate-900/60 lg:block">
      <nav className="space-y-1">
        {items.map((item) => {
          const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname?.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                isActive
                  ? 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-300'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800/60 dark:hover:text-white'
              }`}
            >
              <Icon size={18} />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
