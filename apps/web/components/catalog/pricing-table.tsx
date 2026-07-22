'use client';

import { Pencil, Plus, Trash2 } from 'lucide-react';
import { useState } from 'react';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { PriceFormModal } from '@/components/catalog/price-form-modal';
import { createPrice, deletePrice, updatePrice, type ProductPriceCreateInput } from '@/lib/catalog/pricing';
import type { ProductPriceItem } from '@/lib/types';

interface PricingTableProps {
  productId: string;
  items: ProductPriceItem[];
  onChange: () => Promise<void> | void;
}

export function PricingTable({ productId, items, onChange }: PricingTableProps) {
  const [formTarget, setFormTarget] = useState<ProductPriceItem | null | undefined>(undefined);

  const handleSave = async (data: ProductPriceCreateInput) => {
    if (formTarget) {
      await updatePrice(formTarget.id, data);
    } else {
      await createPrice(data);
    }
    await onChange();
  };

  const handleDelete = async (price: ProductPriceItem) => {
    if (!confirm(`Delete this ${price.currency} price?`)) return;
    await deletePrice(price.id);
    await onChange();
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-slate-900 dark:text-white">Pricing</h3>
        <PermissionGuard permission="catalog.pricing.manage">
          <button type="button" onClick={() => setFormTarget(null)} className="flex items-center gap-1.5 rounded-xl bg-cyan-500 px-3 py-1.5 text-xs font-semibold text-slate-950 transition hover:bg-cyan-400">
            <Plus size={14} /> Add price
          </button>
        </PermissionGuard>
      </div>

      {items.length === 0 ? (
        <EmptyState title="No prices set" description="Add a selling price to make this product purchasable." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">Currency</th>
                <th className="px-4 py-3">Selling price</th>
                <th className="px-4 py-3">MRP</th>
                <th className="px-4 py-3">Region</th>
                <th className="px-4 py-3">Customer group</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {items.map((price) => (
                <tr key={price.id} className="bg-white dark:bg-slate-900/40">
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{price.currency}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{price.selling_price.toFixed(2)}</td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{price.mrp?.toFixed(2) ?? '—'}</td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{price.region ?? 'All'}</td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{price.customer_group ?? 'All'}</td>
                  <td className="px-4 py-3">
                    <PermissionGuard permission="catalog.pricing.manage">
                      <div className="flex justify-end gap-2">
                        <button type="button" onClick={() => setFormTarget(price)} className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white">
                          <Pencil size={16} />
                        </button>
                        <button type="button" onClick={() => handleDelete(price)} className="rounded-lg p-1.5 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10">
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

      {formTarget !== undefined ? (
        <PriceFormModal productId={productId} price={formTarget} onSubmit={handleSave} onClose={() => setFormTarget(undefined)} />
      ) : null}
    </div>
  );
}
