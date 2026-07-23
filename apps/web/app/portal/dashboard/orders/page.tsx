'use client';

import { ShoppingBag } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { fetchMyOrders } from '@/lib/customer-portal/orders';
import type { OrderRead } from '@/lib/types';

const PAGE_SIZE = 20;

export default function PortalOrdersPage() {
  const [items, setItems] = useState<OrderRead[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchMyOrders(undefined, PAGE_SIZE, offset);
        setItems(data.items);
        setTotal(data.total);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load your orders.');
      } finally {
        setLoading(false);
      }
    })();
  }, [offset]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-slate-900 dark:text-white">My orders</h2>
      <FormError message={error} />
      {loading ? (
        <SkeletonRows count={5} />
      ) : items.length === 0 ? (
        <EmptyState icon={ShoppingBag} title="No orders yet" description="Your orders will show up here once you check out." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">Order #</th>
                <th className="px-4 py-3">Total</th>
                <th className="px-4 py-3">Payment</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {items.map((order) => (
                <tr key={order.id} className="bg-white dark:bg-slate-900/40">
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                    <Link href={`/portal/dashboard/orders/${order.id}`} className="hover:text-cyan-600 dark:hover:text-cyan-300">{order.order_number}</Link>
                  </td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{order.currency} {order.total.toFixed(2)}</td>
                  <td className="px-4 py-3 capitalize text-slate-500 dark:text-slate-400">{order.payment_status.replace(/_/g, ' ')}</td>
                  <td className="px-4 py-3 capitalize text-slate-500 dark:text-slate-400">{order.status.replace(/_/g, ' ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {total > 0 ? (
        <div className="flex items-center justify-between text-sm text-slate-500 dark:text-slate-400">
          <span>Page {currentPage} of {totalPages} ({total} total)</span>
          <div className="flex gap-2">
            <button type="button" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))} className="rounded-lg border border-slate-300 px-3 py-1.5 font-medium text-slate-700 disabled:opacity-40 dark:border-slate-700 dark:text-slate-200">Previous</button>
            <button type="button" disabled={offset + PAGE_SIZE >= total} onClick={() => setOffset(offset + PAGE_SIZE)} className="rounded-lg border border-slate-300 px-3 py-1.5 font-medium text-slate-700 disabled:opacity-40 dark:border-slate-700 dark:text-slate-200">Next</button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
