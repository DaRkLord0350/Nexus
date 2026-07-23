'use client';

import { ShoppingCart, User } from 'lucide-react';
import Link from 'next/link';
import type { ReactNode } from 'react';
import { getCustomerToken } from '@/lib/customer-portal/api-client';

export default function ShopLayout({ children }: { children: ReactNode }) {
  const isSignedIn = typeof window !== 'undefined' && !!getCustomerToken();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <header className="flex items-center justify-between border-b border-slate-200 bg-white/80 px-6 py-4 dark:border-slate-800 dark:bg-slate-900/60">
        <Link href="/shop/cart" className="text-xs uppercase tracking-[0.3em] text-cyan-600 dark:text-cyan-300">CommerceOS Shop</Link>
        <div className="flex items-center gap-4">
          <Link href="/shop/cart" className="flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white">
            <ShoppingCart size={16} /> Cart
          </Link>
          <Link
            href={isSignedIn ? '/portal/dashboard' : '/portal/login'}
            className="flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white"
          >
            <User size={16} /> {isSignedIn ? 'My account' : 'Sign in'}
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-6 py-10">{children}</main>
    </div>
  );
}
