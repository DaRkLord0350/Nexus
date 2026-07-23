'use client';

import { Heart, LayoutDashboard, LogOut, MapPin, RotateCcw, ShoppingBag, User } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { ReactNode } from 'react';
import { CustomerAuthProvider, useCustomerAuth } from '@/components/customer-portal/customer-auth-provider';

const NAV_ITEMS = [
  { href: '/portal/dashboard', label: 'Overview', icon: LayoutDashboard },
  { href: '/portal/dashboard/orders', label: 'Orders', icon: ShoppingBag },
  { href: '/portal/dashboard/returns', label: 'Returns', icon: RotateCcw },
  { href: '/portal/dashboard/wishlist', label: 'Wishlist', icon: Heart },
  { href: '/portal/dashboard/addresses', label: 'Addresses', icon: MapPin },
  { href: '/portal/dashboard/profile', label: 'Profile', icon: User },
];

function PortalShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { customer, isLoading, logout } = useCustomerAuth();

  if (isLoading) {
    return <div className="flex min-h-screen items-center justify-center text-slate-500 dark:text-slate-400">Loading…</div>;
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <div className="flex min-h-screen">
        <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white/80 lg:flex lg:flex-col dark:border-slate-800 dark:bg-slate-900/60">
          <div className="px-6 py-6">
            <p className="text-xs uppercase tracking-[0.3em] text-cyan-600 dark:text-cyan-300">CommerceOS</p>
            <p className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">My Account</p>
          </div>
          <nav className="flex-1 space-y-1 px-4">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname === item.href || (item.href !== '/portal/dashboard' && pathname?.startsWith(item.href));
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
          <div className="border-t border-slate-200 px-4 py-4 dark:border-slate-800">
            <button
              type="button"
              onClick={logout}
              className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800/60 dark:hover:text-white"
            >
              <LogOut size={18} /> Sign out
            </button>
          </div>
        </aside>
        <div className="flex flex-1 flex-col">
          <header className="flex items-center justify-between border-b border-slate-200 bg-white/80 px-6 py-4 dark:border-slate-800 dark:bg-slate-900/60">
            <h1 className="text-lg font-semibold text-slate-900 dark:text-white">Welcome{customer ? `, ${customer.first_name}` : ''}</h1>
          </header>
          <section className="flex-1 px-6 py-8 lg:px-10">{children}</section>
        </div>
      </div>
    </div>
  );
}

export default function PortalDashboardLayout({ children }: { children: ReactNode }) {
  return (
    <CustomerAuthProvider>
      <PortalShell>{children}</PortalShell>
    </CustomerAuthProvider>
  );
}
