'use client';

import { Heart, MapPin, RotateCcw, ShoppingBag } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { fetchMyOrders } from '@/lib/customer-portal/orders';
import type { OrderRead } from '@/lib/types';

export default function PortalOverviewPage() {
  const [orders, setOrders] = useState<OrderRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await fetchMyOrders(undefined, 5, 0);
        setOrders(data.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load your orders.');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-4">
        <Link href="/portal/dashboard/orders" className="rounded-2xl border border-slate-200 bg-white p-4 text-center hover:border-cyan-400 dark:border-slate-800 dark:bg-slate-900/60">
          <ShoppingBag className="mx-auto mb-2 text-cyan-600 dark:text-cyan-400" size={22} />
          <p className="text-sm font-medium text-slate-700 dark:text-slate-200">Orders</p>
        </Link>
        <Link href="/portal/dashboard/returns" className="rounded-2xl border border-slate-200 bg-white p-4 text-center hover:border-cyan-400 dark:border-slate-800 dark:bg-slate-900/60">
          <RotateCcw className="mx-auto mb-2 text-cyan-600 dark:text-cyan-400" size={22} />
          <p className="text-sm font-medium text-slate-700 dark:text-slate-200">Returns</p>
        </Link>
        <Link href="/portal/dashboard/wishlist" className="rounded-2xl border border-slate-200 bg-white p-4 text-center hover:border-cyan-400 dark:border-slate-800 dark:bg-slate-900/60">
          <Heart className="mx-auto mb-2 text-cyan-600 dark:text-cyan-400" size={22} />
          <p className="text-sm font-medium text-slate-700 dark:text-slate-200">Wishlist</p>
        </Link>
        <Link href="/portal/dashboard/addresses" className="rounded-2xl border border-slate-200 bg-white p-4 text-center hover:border-cyan-400 dark:border-slate-800 dark:bg-slate-900/60">
          <MapPin className="mx-auto mb-2 text-cyan-600 dark:text-cyan-400" size={22} />
          <p className="text-sm font-medium text-slate-700 dark:text-slate-200">Addresses</p>
        </Link>
      </div>

      <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Recent orders</h2>
      <FormError message={error} />
      {loading ? (
        <SkeletonRows count={3} />
      ) : orders.length === 0 ? (
        <EmptyState icon={ShoppingBag} title="No orders yet" description="Your orders will show up here once you check out." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">Order #</th>
                <th className="px-4 py-3">Total</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {orders.map((order) => (
                <tr key={order.id} className="bg-white dark:bg-slate-900/40">
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                    <Link href={`/portal/dashboard/orders/${order.id}`} className="hover:text-cyan-600 dark:hover:text-cyan-300">{order.order_number}</Link>
                  </td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{order.currency} {order.total.toFixed(2)}</td>
                  <td className="px-4 py-3 capitalize text-slate-500 dark:text-slate-400">{order.status.replace(/_/g, ' ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
