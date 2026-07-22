'use client';

import { AlertTriangle, ArrowLeft, CheckCircle2, XCircle } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError, FormInput } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import {
  cancelCycleCount,
  completeCycleCount,
  fetchCycleCount,
  recordCycleCountItem,
} from '@/lib/inventory/cycle-counts';
import type { CycleCountDetail } from '@/lib/types';

export default function CycleCountDetailPage() {
  const params = useParams<{ id: string }>();
  const cycleCountId = params.id;

  const [cycleCount, setCycleCount] = useState<CycleCountDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draftCounts, setDraftCounts] = useState<Record<string, string>>({});
  const [actionLoading, setActionLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCycleCount(cycleCountId);
      setCycleCount(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load cycle count.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (cycleCountId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cycleCountId]);

  const handleRecord = async (itemId: string) => {
    const value = draftCounts[itemId];
    if (value === undefined || value === '') return;
    try {
      await recordCycleCountItem(cycleCountId, itemId, Number(value));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to record count.');
    }
  };

  const handleComplete = async () => {
    setActionLoading(true);
    try {
      await completeCycleCount(cycleCountId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to complete cycle count.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    setActionLoading(true);
    try {
      await cancelCycleCount(cycleCountId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to cancel cycle count.');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <SkeletonRows count={6} />;

  const canEdit = cycleCount && (cycleCount.status === 'scheduled' || cycleCount.status === 'in_progress');

  return (
    <div className="space-y-6">
      <Link href="/dashboard/inventory/cycle-counts" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
        <ArrowLeft size={14} /> Back to cycle counts
      </Link>

      <FormError message={error} />

      {!cycleCount ? (
        <EmptyState title="Cycle count not found" />
      ) : (
        <>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{cycleCount.count_number}</h2>
                <p className="mt-1 text-sm capitalize text-slate-500 dark:text-slate-400">{cycleCount.status.replace('_', ' ')}</p>
              </div>
              {canEdit ? (
                <div className="flex gap-2">
                  <PermissionGuard permission="inventory.cycle_counts.manage">
                    <button
                      type="button"
                      onClick={handleComplete}
                      disabled={actionLoading}
                      className="flex items-center gap-1.5 rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50"
                    >
                      <CheckCircle2 size={14} /> Complete
                    </button>
                  </PermissionGuard>
                  <PermissionGuard permission="inventory.cycle_counts.manage">
                    <button
                      type="button"
                      onClick={handleCancel}
                      disabled={actionLoading}
                      className="flex items-center gap-1.5 rounded-xl border border-red-300 px-3.5 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50 dark:border-red-500/40 dark:text-red-400 dark:hover:bg-red-500/10"
                    >
                      <XCircle size={14} /> Cancel
                    </button>
                  </PermissionGuard>
                </div>
              ) : null}
            </div>
          </div>

          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Items ({cycleCount.items.length})</h3>

          {cycleCount.items.length === 0 ? (
            <EmptyState title="No items to count" />
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                  <tr>
                    <th className="px-4 py-3">Product</th>
                    <th className="px-4 py-3">Expected</th>
                    <th className="px-4 py-3">Actual</th>
                    <th className="px-4 py-3">Variance</th>
                    {canEdit ? <th className="px-4 py-3 text-right">Record count</th> : null}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {cycleCount.items.map((item) => (
                    <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                      <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{item.product_id.slice(0, 8)}…</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.expected_quantity}</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.actual_quantity ?? '—'}</td>
                      <td className="px-4 py-3">
                        {item.variance != null ? (
                          <span className={`inline-flex items-center gap-1 font-medium ${item.variance !== 0 ? 'text-amber-600 dark:text-amber-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                            {item.variance !== 0 ? <AlertTriangle size={13} /> : null}
                            {item.variance > 0 ? `+${item.variance}` : item.variance}
                          </span>
                        ) : '—'}
                      </td>
                      {canEdit ? (
                        <td className="px-4 py-3">
                          <div className="flex justify-end gap-2">
                            <FormInput
                              type="number"
                              min={0}
                              placeholder="Actual qty"
                              className="w-28"
                              value={draftCounts[item.id] ?? ''}
                              onChange={(e) => setDraftCounts((prev) => ({ ...prev, [item.id]: e.target.value }))}
                            />
                            <PermissionGuard permission="inventory.cycle_counts.manage">
                              <button
                                type="button"
                                onClick={() => handleRecord(item.id)}
                                className="rounded-lg bg-cyan-500 px-3 py-1.5 text-xs font-semibold text-slate-950 hover:bg-cyan-400"
                              >
                                Record
                              </button>
                            </PermissionGuard>
                          </div>
                        </td>
                      ) : null}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
