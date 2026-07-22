'use client';

import { useEffect, useState } from 'react';
import { Modal } from '@/components/ui/modal';
import { EmptyState } from '@/components/ui/empty-state';
import { SkeletonRows } from '@/components/ui/skeleton';
import { fetchInventoryTransactions } from '@/lib/inventory/stock';
import type { InventoryTransactionItem } from '@/lib/types';

interface InventoryHistoryModalProps {
  inventoryId: string;
  onClose: () => void;
}

export function InventoryHistoryModal({ inventoryId, onClose }: InventoryHistoryModalProps) {
  const [items, setItems] = useState<InventoryTransactionItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInventoryTransactions({ inventoryId, limit: 50 })
      .then((data) => setItems(data.items))
      .finally(() => setLoading(false));
  }, [inventoryId]);

  return (
    <Modal title="Transaction history" onClose={onClose}>
      <div className="max-h-[60vh] space-y-2 overflow-y-auto">
        {loading ? (
          <SkeletonRows count={4} />
        ) : items.length === 0 ? (
          <EmptyState title="No transactions yet" />
        ) : (
          <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                <tr>
                  <th className="px-3 py-2">Type</th>
                  <th className="px-3 py-2">Qty</th>
                  <th className="px-3 py-2">Before → After</th>
                  <th className="px-3 py-2">When</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {items.map((item) => (
                  <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                    <td className="px-3 py-2 capitalize text-slate-700 dark:text-slate-200">{item.type.replace('_', ' ')}</td>
                    <td className={`px-3 py-2 font-medium ${item.quantity < 0 ? 'text-red-600 dark:text-red-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                      {item.quantity > 0 ? `+${item.quantity}` : item.quantity}
                    </td>
                    <td className="px-3 py-2 text-slate-500 dark:text-slate-400">
                      {item.quantity_before ?? '—'} → {item.quantity_after ?? '—'}
                    </td>
                    <td className="px-3 py-2 text-slate-500 dark:text-slate-400">{new Date(item.occurred_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Modal>
  );
}
