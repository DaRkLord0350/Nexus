'use client';

import { Receipt } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { RefundFormModal } from '@/components/orders/refund-form-modal';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError, FormInput } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { createRefund, fetchRefunds, type RefundCreateInput } from '@/lib/orders/refunds';
import type { RefundRead, RefundStatus } from '@/lib/types';

const PAGE_SIZE = 25;

const STATUS_OPTIONS: RefundStatus[] = ['requested', 'approved', 'rejected', 'processing', 'completed', 'failed'];

const STATUS_STYLES: Record<RefundStatus, string> = {
  requested: 'text-amber-600 dark:text-amber-400',
  approved: 'text-cyan-600 dark:text-cyan-400',
  rejected: 'text-red-600 dark:text-red-400',
  processing: 'text-blue-600 dark:text-blue-400',
  completed: 'text-emerald-600 dark:text-emerald-400',
  failed: 'text-red-600 dark:text-red-400',
};

export default function RefundsPage() {
  const [items, setItems] = useState<RefundRead[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showForm, setShowForm] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRefunds({ q: q || undefined, status: statusFilter || undefined, limit: PAGE_SIZE, offset });
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load refunds.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offset]);

  const applyFilters = () => {
    setOffset(0);
    load();
  };

  const handleSave = async (data: RefundCreateInput) => {
    await createRefund(data);
    await load();
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Refunds</h2>
        <PermissionGuard permission="refunds.manage">
          <button type="button" onClick={() => setShowForm(true)} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400">
            New refund
          </button>
        </PermissionGuard>
      </div>

      <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60 sm:grid-cols-3">
        <FormInput placeholder="Search by refund #…" value={q} onChange={(e) => setQ(e.target.value)} />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <button type="button" onClick={applyFilters} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400">
          Apply filters
        </button>
      </div>

      <FormError message={error} />

      {loading ? (
        <SkeletonRows count={6} />
      ) : items.length === 0 ? (
        <EmptyState icon={Receipt} title="No refunds found" description="Refund requests will appear here once created." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">Refund #</th>
                <th className="px-4 py-3">Method</th>
                <th className="px-4 py-3">Amount</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {items.map((item) => (
                <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                    <Link href={`/dashboard/orders/refunds/${item.id}`} className="hover:text-cyan-600 dark:hover:text-cyan-300">{item.refund_number}</Link>
                  </td>
                  <td className="px-4 py-3 capitalize text-slate-600 dark:text-slate-300">{item.method.replace(/_/g, ' ')}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.currency} {item.amount.toFixed(2)}</td>
                  <td className="px-4 py-3">
                    <span className={`capitalize ${STATUS_STYLES[item.status]}`}>{item.status}</span>
                  </td>
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

      {showForm ? <RefundFormModal onSubmit={handleSave} onClose={() => setShowForm(false)} /> : null}
    </div>
  );
}
