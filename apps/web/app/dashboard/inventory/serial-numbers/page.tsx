'use client';

import { Barcode as ScanIcon, Pencil, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { SerialNumberFormModal } from '@/components/inventory/serial-number-form-modal';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError, FormInput } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import {
  bulkDeleteSerialNumbers,
  createSerialNumber,
  deleteSerialNumber,
  fetchSerialNumbers,
  importSerialNumbers,
  scanSerialNumber,
  updateSerialNumber,
  type SerialNumberCreateInput,
  type SerialNumberImportInput,
} from '@/lib/inventory/serial-numbers';
import type { SerialNumberItem, SerialStatus } from '@/lib/types';

const PAGE_SIZE = 25;

const STATUS_STYLES: Record<SerialStatus, string> = {
  available: 'text-emerald-600 dark:text-emerald-400',
  reserved: 'text-amber-600 dark:text-amber-400',
  sold: 'text-slate-500 dark:text-slate-400',
  returned: 'text-cyan-600 dark:text-cyan-400',
  damaged: 'text-red-600 dark:text-red-400',
};

export default function SerialNumbersPage() {
  const [items, setItems] = useState<SerialNumberItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [scanValue, setScanValue] = useState('');
  const [scanResult, setScanResult] = useState<SerialNumberItem | null | undefined>(undefined);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [showForm, setShowForm] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchSerialNumbers({ q: q || undefined, status: statusFilter || undefined, limit: PAGE_SIZE, offset });
      setItems(data.items);
      setTotal(data.total);
      setSelected(new Set());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load serial numbers.');
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

  const handleScan = async () => {
    if (!scanValue.trim()) return;
    try {
      const result = await scanSerialNumber(scanValue.trim());
      setScanResult(result);
    } catch {
      setScanResult(null);
    }
  };

  const handleSave = async (data: SerialNumberCreateInput) => {
    await createSerialNumber(data);
    await load();
  };

  const handleImport = async (data: SerialNumberImportInput) => {
    const result = await importSerialNumbers(data);
    await load();
    return result;
  };

  const handleStatusChange = async (item: SerialNumberItem, status: SerialStatus) => {
    await updateSerialNumber(item.id, { status });
    await load();
  };

  const handleDelete = async (item: SerialNumberItem) => {
    if (!confirm(`Delete serial "${item.serial}"?`)) return;
    try {
      await deleteSerialNumber(item.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete serial number.');
    }
  };

  const handleBulkDelete = async () => {
    if (selected.size === 0) return;
    if (!confirm(`Delete ${selected.size} selected serial(s)?`)) return;
    try {
      await bulkDeleteSerialNumbers(Array.from(selected));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete selected serials.');
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
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Serial Numbers</h2>
        <PermissionGuard permission="inventory.serials.manage">
          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400"
          >
            Add serials
          </button>
        </PermissionGuard>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
        <div className="mb-2 flex items-center gap-1.5 text-sm font-medium text-slate-700 dark:text-slate-300">
          <ScanIcon size={15} /> Scan lookup
        </div>
        <div className="flex gap-2">
          <FormInput placeholder="Scan or type a serial…" value={scanValue} onChange={(e) => setScanValue(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') handleScan(); }} />
          <button type="button" onClick={handleScan} className="shrink-0 rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400">
            Lookup
          </button>
        </div>
        {scanResult !== undefined ? (
          <div className="mt-3 text-sm">
            {scanResult ? (
              <span className="text-slate-700 dark:text-slate-300">
                Found: <span className="font-semibold">{scanResult.serial}</span> · Status: <span className={STATUS_STYLES[scanResult.status]}>{scanResult.status}</span> · Warehouse: {scanResult.warehouse_id}
              </span>
            ) : (
              <span className="text-red-600 dark:text-red-400">No matching serial found.</span>
            )}
          </div>
        ) : null}
      </div>

      <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60 sm:grid-cols-3">
        <FormInput placeholder="Search by serial…" value={q} onChange={(e) => setQ(e.target.value)} />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
        >
          <option value="">All statuses</option>
          <option value="available">Available</option>
          <option value="reserved">Reserved</option>
          <option value="sold">Sold</option>
          <option value="returned">Returned</option>
          <option value="damaged">Damaged</option>
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
        <PermissionGuard permission="inventory.serials.manage">
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
        <EmptyState icon={ScanIcon} title="No serial numbers found" description="Track individually serialized units such as electronics and equipment." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">
                  <input type="checkbox" checked={selected.size === items.length} onChange={toggleSelectAll} />
                </th>
                <th className="px-4 py-3">Serial</th>
                <th className="px-4 py-3">Product</th>
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
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{item.serial}</td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{item.product_id.slice(0, 8)}…</td>
                  <td className="px-4 py-3">
                    <PermissionGuard permission="inventory.serials.manage" fallback={<span className={STATUS_STYLES[item.status]}>{item.status}</span>}>
                      <select
                        value={item.status}
                        onChange={(e) => handleStatusChange(item, e.target.value as SerialStatus)}
                        className={`rounded-lg border border-slate-300 bg-white px-2 py-1 text-xs dark:border-slate-700 dark:bg-slate-950/60 ${STATUS_STYLES[item.status]}`}
                      >
                        <option value="available">Available</option>
                        <option value="reserved">Reserved</option>
                        <option value="sold">Sold</option>
                        <option value="returned">Returned</option>
                        <option value="damaged">Damaged</option>
                      </select>
                    </PermissionGuard>
                  </td>
                  <td className="px-4 py-3">
                    <PermissionGuard permission="inventory.serials.manage">
                      <div className="flex justify-end gap-2">
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

      {showForm ? (
        <SerialNumberFormModal onSubmit={handleSave} onImport={handleImport} onClose={() => setShowForm(false)} />
      ) : null}
    </div>
  );
}
