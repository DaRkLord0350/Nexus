'use client';

import { ClipboardCheck } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { CycleCountFormModal } from '@/components/inventory/cycle-count-form-modal';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { createCycleCount, fetchCycleCounts, type CycleCountCreateInput } from '@/lib/inventory/cycle-counts';
import { fetchWarehouses } from '@/lib/inventory/warehouses';
import type { CycleCountItem, CycleCountStatus, WarehouseItem } from '@/lib/types';

const PAGE_SIZE = 25;

const STATUS_STYLES: Record<CycleCountStatus, string> = {
  scheduled: 'text-slate-500 dark:text-slate-400',
  in_progress: 'text-amber-600 dark:text-amber-400',
  completed: 'text-emerald-600 dark:text-emerald-400',
  cancelled: 'text-red-600 dark:text-red-400',
};

export default function CycleCountsPage() {
  const [items, setItems] = useState<CycleCountItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [warehouses, setWarehouses] = useState<WarehouseItem[]>([]);
  const [warehouseNames, setWarehouseNames] = useState<Record<string, string>>({});
  const [showForm, setShowForm] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [data, warehousesData] = await Promise.all([
        fetchCycleCounts({ status: statusFilter || undefined, limit: PAGE_SIZE, offset }),
        fetchWarehouses({ limit: 200 }),
      ]);
      setItems(data.items);
      setTotal(data.total);
      setWarehouses(warehousesData.items);
      setWarehouseNames(Object.fromEntries(warehousesData.items.map((w) => [w.id, w.name])));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load cycle counts.');
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

  const handleSave = async (data: CycleCountCreateInput) => {
    await createCycleCount(data);
    await load();
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Cycle Counts</h2>
        <PermissionGuard permission="inventory.cycle_counts.create">
          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400"
          >
            New cycle count
          </button>
        </PermissionGuard>
      </div>

      <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60 sm:grid-cols-2">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
        >
          <option value="">All statuses</option>
          <option value="scheduled">Scheduled</option>
          <option value="in_progress">In progress</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <button
          type="button"
          onClick={applyFilters}
          className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400"
        >
          Apply filters
        </button>
      </div>

      <FormError message={error} />

      {loading ? (
        <SkeletonRows count={6} />
      ) : items.length === 0 ? (
        <EmptyState icon={ClipboardCheck} title="No cycle counts found" description="Schedule regular counts to reconcile expected vs. actual stock." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">Count #</th>
                <th className="px-4 py-3">Warehouse</th>
                <th className="px-4 py-3">Scheduled</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {items.map((item) => (
                <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                    <Link href={`/dashboard/inventory/cycle-counts/${item.id}`} className="hover:text-cyan-600 dark:hover:text-cyan-300">
                      {item.count_number}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{warehouseNames[item.warehouse_id] ?? item.warehouse_id}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.scheduled_date ? new Date(item.scheduled_date).toLocaleDateString() : '—'}</td>
                  <td className="px-4 py-3">
                    <span className={`capitalize ${STATUS_STYLES[item.status]}`}>{item.status.replace('_', ' ')}</span>
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
            <button type="button" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))} className="rounded-lg border border-slate-300 px-3 py-1.5 font-medium text-slate-700 disabled:opacity-40 dark:border-slate-700 dark:text-slate-200">
              Previous
            </button>
            <button type="button" disabled={offset + PAGE_SIZE >= total} onClick={() => setOffset(offset + PAGE_SIZE)} className="rounded-lg border border-slate-300 px-3 py-1.5 font-medium text-slate-700 disabled:opacity-40 dark:border-slate-700 dark:text-slate-200">
              Next
            </button>
          </div>
        </div>
      ) : null}

      {showForm ? (
        <CycleCountFormModal warehouses={warehouses} onSubmit={handleSave} onClose={() => setShowForm(false)} />
      ) : null}
    </div>
  );
}
