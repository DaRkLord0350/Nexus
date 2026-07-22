'use client';

import { AlertTriangle, Boxes, Pencil, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { BatchFormModal } from '@/components/inventory/batch-form-modal';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError, FormInput } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import {
  bulkDeleteBatches,
  createBatch,
  deleteBatch,
  fetchBatches,
  updateBatch,
  type BatchCreateInput,
  type BatchUpdateInput,
} from '@/lib/inventory/batches';
import { fetchWarehouses } from '@/lib/inventory/warehouses';
import type { BatchItem } from '@/lib/types';

const PAGE_SIZE = 25;

function isExpiringSoon(expiryDate?: string | null): boolean {
  if (!expiryDate) return false;
  const days = (new Date(expiryDate).getTime() - Date.now()) / (1000 * 60 * 60 * 24);
  return days <= 30;
}

export default function BatchesPage() {
  const [items, setItems] = useState<BatchItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [warehouseFilter, setWarehouseFilter] = useState('');
  const [warehouseNames, setWarehouseNames] = useState<Record<string, string>>({});
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [formTarget, setFormTarget] = useState<BatchItem | null | undefined>(undefined);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [data, warehousesData] = await Promise.all([
        fetchBatches({ q: q || undefined, status: statusFilter || undefined, warehouseId: warehouseFilter || undefined, limit: PAGE_SIZE, offset }),
        fetchWarehouses({ limit: 200 }),
      ]);
      setItems(data.items);
      setTotal(data.total);
      setWarehouseNames(Object.fromEntries(warehousesData.items.map((w) => [w.id, w.name])));
      setSelected(new Set());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load batches.');
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

  const handleSave = async (data: BatchCreateInput | BatchUpdateInput) => {
    if (formTarget) {
      await updateBatch(formTarget.id, data as BatchUpdateInput);
    } else {
      await createBatch(data as BatchCreateInput);
    }
    await load();
  };

  const handleDelete = async (batch: BatchItem) => {
    if (!confirm(`Delete batch "${batch.batch_number}"?`)) return;
    try {
      await deleteBatch(batch.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete batch.');
    }
  };

  const handleBulkDelete = async () => {
    if (selected.size === 0) return;
    if (!confirm(`Delete ${selected.size} selected batch(es)?`)) return;
    try {
      await bulkDeleteBatches(Array.from(selected));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete selected batches.');
    }
  };

  const toggleSelected = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    setSelected((prev) => (prev.size === items.length ? new Set() : new Set(items.map((i) => i.id))));
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Batches</h2>
        <PermissionGuard permission="inventory.batches.manage">
          <button
            type="button"
            onClick={() => setFormTarget(null)}
            className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400"
          >
            New batch
          </button>
        </PermissionGuard>
      </div>

      <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60 sm:grid-cols-4">
        <FormInput placeholder="Search by batch number…" value={q} onChange={(e) => setQ(e.target.value)} />
        <select
          value={warehouseFilter}
          onChange={(e) => setWarehouseFilter(e.target.value)}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
        >
          <option value="">All warehouses</option>
          {Object.entries(warehouseNames).map(([id, name]) => (
            <option key={id} value={id}>{name}</option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
        >
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="depleted">Depleted</option>
          <option value="expired">Expired</option>
          <option value="quarantined">Quarantined</option>
          <option value="recalled">Recalled</option>
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

      {selected.size > 0 ? (
        <PermissionGuard permission="inventory.batches.manage">
          <div className="flex items-center justify-between rounded-xl border border-cyan-300 bg-cyan-50 px-4 py-2.5 text-sm dark:border-cyan-700 dark:bg-cyan-500/10">
            <span className="text-cyan-800 dark:text-cyan-200">{selected.size} selected</span>
            <button type="button" onClick={handleBulkDelete} className="flex items-center gap-1.5 font-semibold text-red-600 dark:text-red-400">
              <Trash2 size={14} /> Delete selected
            </button>
          </div>
        </PermissionGuard>
      ) : null}

      {loading ? (
        <SkeletonRows count={6} />
      ) : items.length === 0 ? (
        <EmptyState icon={Boxes} title="No batches found" description="Track batches by lot number for FIFO/FEFO stock rotation and expiry management." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">
                  <input type="checkbox" checked={selected.size === items.length} onChange={toggleSelectAll} />
                </th>
                <th className="px-4 py-3">Batch #</th>
                <th className="px-4 py-3">Warehouse</th>
                <th className="px-4 py-3">Remaining</th>
                <th className="px-4 py-3">Expiry</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {items.map((item) => (
                <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                  <td className="px-4 py-3">
                    <input type="checkbox" checked={selected.has(item.id)} onChange={() => toggleSelected(item.id)} />
                  </td>
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{item.batch_number}</td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{warehouseNames[item.warehouse_id] ?? item.warehouse_id}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.remaining_quantity} / {item.received_quantity}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1 ${isExpiringSoon(item.expiry_date) ? 'font-medium text-amber-600 dark:text-amber-400' : 'text-slate-600 dark:text-slate-300'}`}>
                      {isExpiringSoon(item.expiry_date) ? <AlertTriangle size={13} /> : null}
                      {item.expiry_date ? new Date(item.expiry_date).toLocaleDateString() : '—'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300 capitalize">{item.status}</td>
                  <td className="px-4 py-3">
                    <PermissionGuard permission="inventory.batches.manage">
                      <div className="flex justify-end gap-2">
                        <button type="button" onClick={() => setFormTarget(item)} className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white">
                          <Pencil size={16} />
                        </button>
                        <button type="button" onClick={() => handleDelete(item)} className="rounded-lg p-1.5 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10">
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </PermissionGuard>
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

      {formTarget !== undefined ? (
        <BatchFormModal batch={formTarget} onSubmit={handleSave} onClose={() => setFormTarget(undefined)} />
      ) : null}
    </div>
  );
}
