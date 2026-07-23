'use client';

import { Pencil, RefreshCw, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { ReorderRuleFormModal } from '@/components/inventory/reorder-rule-form-modal';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import {
  bulkDeleteReorderRules,
  createReorderRule,
  deleteReorderRule,
  fetchReorderRules,
  updateReorderRule,
  type ReorderRuleCreateInput,
  type ReorderRuleUpdateInput,
} from '@/lib/inventory/reorder-rules';
import { fetchWarehouses } from '@/lib/inventory/warehouses';
import type { ReorderRuleItem, WarehouseItem } from '@/lib/types';

const PAGE_SIZE = 25;

export default function ReorderRulesPage() {
  const [items, setItems] = useState<ReorderRuleItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [warehouses, setWarehouses] = useState<WarehouseItem[]>([]);
  const [warehouseNames, setWarehouseNames] = useState<Record<string, string>>({});
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [formTarget, setFormTarget] = useState<ReorderRuleItem | null | undefined>(undefined);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [data, warehousesData] = await Promise.all([
        fetchReorderRules({ limit: PAGE_SIZE, offset }),
        fetchWarehouses({ limit: 200 }),
      ]);
      setItems(data.items);
      setTotal(data.total);
      setWarehouses(warehousesData.items);
      setWarehouseNames(Object.fromEntries(warehousesData.items.map((w) => [w.id, w.name])));
      setSelected(new Set());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load reorder rules.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offset]);

  const handleSave = async (data: ReorderRuleCreateInput | ReorderRuleUpdateInput) => {
    if (formTarget) {
      await updateReorderRule(formTarget.id, data as ReorderRuleUpdateInput);
    } else {
      await createReorderRule(data as ReorderRuleCreateInput);
    }
    await load();
  };

  const handleDelete = async (rule: ReorderRuleItem) => {
    if (!confirm('Delete this reorder rule?')) return;
    try {
      await deleteReorderRule(rule.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete reorder rule.');
    }
  };

  const handleBulkDelete = async () => {
    if (selected.size === 0) return;
    if (!confirm(`Delete ${selected.size} selected rule(s)?`)) return;
    try {
      await bulkDeleteReorderRules(Array.from(selected));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete selected rules.');
    }
  };

  const toggleSelected = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Reorder Rules</h2>
        <PermissionGuard permission="inventory.reorder_rules.manage">
          <button
            type="button"
            onClick={() => setFormTarget(null)}
            className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400"
          >
            New reorder rule
          </button>
        </PermissionGuard>
      </div>

      <FormError message={error} />

      {selected.size > 0 ? (
        <PermissionGuard permission="inventory.reorder_rules.manage">
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
        <EmptyState icon={RefreshCw} title="No reorder rules found" description="Set minimum stock thresholds to get suggested reorder quantities on low-stock alerts." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">
                  <input type="checkbox" checked={selected.size === items.length} onChange={() => setSelected(selected.size === items.length ? new Set() : new Set(items.map((i) => i.id)))} />
                </th>
                <th className="px-4 py-3">Product</th>
                <th className="px-4 py-3">Warehouse</th>
                <th className="px-4 py-3">Min / Max</th>
                <th className="px-4 py-3">Reorder Qty</th>
                <th className="px-4 py-3">Supplier</th>
                <th className="px-4 py-3">Active</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {items.map((item) => (
                <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                  <td className="px-4 py-3">
                    <input type="checkbox" checked={selected.has(item.id)} onChange={() => toggleSelected(item.id)} />
                  </td>
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{item.product_id.slice(0, 8)}…</td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{warehouseNames[item.warehouse_id] ?? item.warehouse_id}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.minimum_stock} / {item.maximum_stock ?? '—'}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.reorder_quantity}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.supplier_name ?? '—'}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.is_active ? 'Yes' : 'No'}</td>
                  <td className="px-4 py-3">
                    <PermissionGuard permission="inventory.reorder_rules.manage">
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
        <ReorderRuleFormModal rule={formTarget} warehouses={warehouses} onSubmit={handleSave} onClose={() => setFormTarget(undefined)} />
      ) : null}
    </div>
  );
}
