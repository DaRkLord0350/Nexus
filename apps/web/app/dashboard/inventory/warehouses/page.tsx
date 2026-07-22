'use client';

import { Pencil, Star, Trash2, Warehouse as WarehouseIcon } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { WarehouseFormModal } from '@/components/inventory/warehouse-form-modal';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError, FormInput } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import {
  bulkDeleteWarehouses,
  createWarehouse,
  deleteWarehouse,
  fetchWarehouses,
  setDefaultWarehouse,
  updateWarehouse,
  type WarehouseCreateInput,
} from '@/lib/inventory/warehouses';
import type { WarehouseItem } from '@/lib/types';

const PAGE_SIZE = 25;

export default function WarehousesPage() {
  const [items, setItems] = useState<WarehouseItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [formTarget, setFormTarget] = useState<WarehouseItem | null | undefined>(undefined);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchWarehouses({ q: q || undefined, type: typeFilter || undefined, limit: PAGE_SIZE, offset });
      setItems(data.items);
      setTotal(data.total);
      setSelected(new Set());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load warehouses.');
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

  const handleSave = async (data: WarehouseCreateInput) => {
    if (formTarget) {
      await updateWarehouse(formTarget.id, data);
    } else {
      await createWarehouse(data);
    }
    await load();
  };

  const handleDelete = async (warehouse: WarehouseItem) => {
    if (!confirm(`Delete "${warehouse.name}"?`)) return;
    try {
      await deleteWarehouse(warehouse.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete warehouse.');
    }
  };

  const handleSetDefault = async (warehouse: WarehouseItem) => {
    try {
      await setDefaultWarehouse(warehouse.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to set default warehouse.');
    }
  };

  const handleBulkDelete = async () => {
    if (selected.size === 0) return;
    if (!confirm(`Delete ${selected.size} selected warehouse(s)?`)) return;
    try {
      await bulkDeleteWarehouses(Array.from(selected));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete selected warehouses.');
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
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Warehouses</h2>
        <PermissionGuard permission="inventory.warehouses.manage">
          <button
            type="button"
            onClick={() => setFormTarget(null)}
            className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400"
          >
            New warehouse
          </button>
        </PermissionGuard>
      </div>

      <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60 sm:grid-cols-3">
        <FormInput placeholder="Search by name or code…" value={q} onChange={(e) => setQ(e.target.value)} />
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
        >
          <option value="">All types</option>
          <option value="main">Main</option>
          <option value="retail">Retail</option>
          <option value="returns">Returns</option>
          <option value="third_party">Third-party (3PL)</option>
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
        <PermissionGuard permission="inventory.warehouses.manage">
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
        <EmptyState icon={WarehouseIcon} title="No warehouses found" description="Create your first warehouse to start tracking inventory." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">
                  <input type="checkbox" checked={selected.size === items.length} onChange={toggleSelectAll} />
                </th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Code</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Location</th>
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
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                    <Link href={`/dashboard/inventory/warehouses/${item.id}`} className="hover:text-cyan-600 dark:hover:text-cyan-300">
                      {item.name}
                    </Link>
                    {item.is_default ? (
                      <span className="ml-2 inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-500/10 dark:text-amber-300">
                        <Star size={11} /> Default
                      </span>
                    ) : null}
                  </td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{item.code}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300 capitalize">{item.warehouse_type.replace('_', ' ')}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{[item.city, item.country].filter(Boolean).join(', ') || '—'}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.is_active ? 'Active' : 'Inactive'}</td>
                  <td className="px-4 py-3">
                    <PermissionGuard permission="inventory.warehouses.manage">
                      <div className="flex justify-end gap-2">
                        {!item.is_default ? (
                          <button type="button" onClick={() => handleSetDefault(item)} title="Set as default" className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white">
                            <Star size={16} />
                          </button>
                        ) : null}
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
        <WarehouseFormModal warehouse={formTarget} onSubmit={handleSave} onClose={() => setFormTarget(undefined)} />
      ) : null}
    </div>
  );
}
