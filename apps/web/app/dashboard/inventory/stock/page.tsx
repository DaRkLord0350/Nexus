'use client';

import { AlertTriangle, History, Pencil, PackageSearch } from 'lucide-react';
import { useEffect, useState } from 'react';
import { InventoryEditModal } from '@/components/inventory/inventory-edit-modal';
import { InventoryHistoryModal } from '@/components/inventory/inventory-history-modal';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { fetchProducts } from '@/lib/catalog/products';
import { fetchInventory, updateInventoryRecord, type InventoryUpdateInput } from '@/lib/inventory/stock';
import { fetchWarehouses } from '@/lib/inventory/warehouses';
import type { InventoryItem } from '@/lib/types';

const PAGE_SIZE = 25;

export default function InventoryStockPage() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [warehouseFilter, setWarehouseFilter] = useState('');
  const [lowStockOnly, setLowStockOnly] = useState(false);
  const [warehouseNames, setWarehouseNames] = useState<Record<string, string>>({});
  const [productNames, setProductNames] = useState<Record<string, string>>({});
  const [editTarget, setEditTarget] = useState<InventoryItem | null>(null);
  const [historyTarget, setHistoryTarget] = useState<string | null>(null);

  const loadLookups = async () => {
    try {
      const [warehousesData, productsData] = await Promise.all([
        fetchWarehouses({ limit: 200 }),
        fetchProducts({ limit: 200 }),
      ]);
      setWarehouseNames(Object.fromEntries(warehousesData.items.map((w) => [w.id, w.name])));
      setProductNames(Object.fromEntries(productsData.items.map((p) => [p.id, p.name])));
    } catch {
      // Lookups are cosmetic (name display) — silently fall back to raw ids.
    }
  };

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchInventory({
        warehouseId: warehouseFilter || undefined,
        lowStockOnly: lowStockOnly || undefined,
        limit: PAGE_SIZE,
        offset,
      });
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load inventory.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLookups();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offset]);

  const applyFilters = () => {
    setOffset(0);
    load();
  };

  const handleSaveEdit = async (data: InventoryUpdateInput) => {
    if (!editTarget) return;
    await updateInventoryRecord(editTarget.id, data);
    await load();
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Inventory</h2>
      </div>

      <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60 sm:grid-cols-4">
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
        <label className="flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-300">
          <input type="checkbox" checked={lowStockOnly} onChange={(e) => setLowStockOnly(e.target.checked)} />
          Low stock only
        </label>
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
        <EmptyState icon={PackageSearch} title="No inventory records found" description="Inventory records are created automatically as stock moves in and out of warehouses." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">Product</th>
                <th className="px-4 py-3">Warehouse</th>
                <th className="px-4 py-3">Available</th>
                <th className="px-4 py-3">Reserved</th>
                <th className="px-4 py-3">Incoming</th>
                <th className="px-4 py-3">Reorder point</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {items.map((item) => {
                const isLow = item.reorder_point != null && item.quantity_available <= item.reorder_point;
                return (
                  <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                      {productNames[item.product_id] ?? item.product_id}
                      {item.variant_id ? <span className="ml-1 text-xs text-slate-400">(variant)</span> : null}
                    </td>
                    <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{warehouseNames[item.warehouse_id] ?? item.warehouse_id}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 font-medium ${isLow ? 'text-amber-600 dark:text-amber-400' : 'text-slate-900 dark:text-white'}`}>
                        {isLow ? <AlertTriangle size={13} /> : null}
                        {item.quantity_available}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.quantity_reserved}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.quantity_incoming}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.reorder_point ?? '—'}</td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-2">
                        <button type="button" onClick={() => setHistoryTarget(item.id)} title="Transaction history" className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white">
                          <History size={16} />
                        </button>
                        <PermissionGuard permission="inventory.stock.manage">
                          <button type="button" onClick={() => setEditTarget(item)} title="Edit configuration" className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white">
                            <Pencil size={16} />
                          </button>
                        </PermissionGuard>
                      </div>
                    </td>
                  </tr>
                );
              })}
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

      {editTarget ? (
        <InventoryEditModal inventory={editTarget} onSubmit={handleSaveEdit} onClose={() => setEditTarget(null)} />
      ) : null}

      {historyTarget ? (
        <InventoryHistoryModal inventoryId={historyTarget} onClose={() => setHistoryTarget(null)} />
      ) : null}
    </div>
  );
}
