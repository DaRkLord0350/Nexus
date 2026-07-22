'use client';

import { Plus, Trash2 } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { StockTransferCreateInput, StockTransferLineItemInput } from '@/lib/inventory/transfers';
import type { WarehouseItem } from '@/lib/types';

interface TransferFormModalProps {
  warehouses: WarehouseItem[];
  onSubmit: (data: StockTransferCreateInput) => Promise<void>;
  onClose: () => void;
}

interface DraftItem extends StockTransferLineItemInput {
  key: string;
}

export function TransferFormModal({ warehouses, onSubmit, onClose }: TransferFormModalProps) {
  const [fromWarehouseId, setFromWarehouseId] = useState(warehouses[0]?.id ?? '');
  const [toWarehouseId, setToWarehouseId] = useState(warehouses[1]?.id ?? '');
  const [notes, setNotes] = useState('');
  const [items, setItems] = useState<DraftItem[]>([{ key: crypto.randomUUID(), product_id: '', quantity_requested: 1 }]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addItemRow = () => {
    setItems((prev) => [...prev, { key: crypto.randomUUID(), product_id: '', quantity_requested: 1 }]);
  };

  const removeItemRow = (key: string) => {
    setItems((prev) => prev.filter((item) => item.key !== key));
  };

  const updateItem = (key: string, patch: Partial<DraftItem>) => {
    setItems((prev) => prev.map((item) => (item.key === key ? { ...item, ...patch } : item)));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!fromWarehouseId || !toWarehouseId) return;
    if (fromWarehouseId === toWarehouseId) {
      setError('Source and destination warehouse must be different.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const validItems = items.filter((item) => item.product_id.trim() && item.quantity_requested > 0);
      await onSubmit({
        from_warehouse_id: fromWarehouseId,
        to_warehouse_id: toWarehouseId,
        notes: notes.trim() || undefined,
        items: validItems.map(({ key, ...rest }) => rest),
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create stock transfer.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title="New stock transfer" onClose={onClose}>
      <form onSubmit={handleSubmit} className="max-h-[75vh] space-y-4 overflow-y-auto pr-1">
        <FormError message={error} />

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="From warehouse" htmlFor="tr-from" />
            <select
              id="tr-from"
              value={fromWarehouseId}
              onChange={(e) => setFromWarehouseId(e.target.value)}
              required
              className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
            >
              <option value="">Select…</option>
              {warehouses.map((w) => (
                <option key={w.id} value={w.id}>{w.name}</option>
              ))}
            </select>
          </div>
          <div>
            <FormField label="To warehouse" htmlFor="tr-to" />
            <select
              id="tr-to"
              value={toWarehouseId}
              onChange={(e) => setToWarehouseId(e.target.value)}
              required
              className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
            >
              <option value="">Select…</option>
              {warehouses.map((w) => (
                <option key={w.id} value={w.id}>{w.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <FormField label="Notes" htmlFor="tr-notes" />
          <FormInput id="tr-notes" value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <FormField label="Line items" htmlFor="tr-items" />
            <button type="button" onClick={addItemRow} className="flex items-center gap-1 text-xs font-semibold text-cyan-600 dark:text-cyan-400">
              <Plus size={12} /> Add item
            </button>
          </div>
          {items.map((item) => (
            <div key={item.key} className="grid grid-cols-[2fr_1fr_auto] gap-2">
              <FormInput placeholder="Product ID" value={item.product_id} onChange={(e) => updateItem(item.key, { product_id: e.target.value })} />
              <FormInput type="number" min={1} placeholder="Qty" value={item.quantity_requested} onChange={(e) => updateItem(item.key, { quantity_requested: Number(e.target.value) })} />
              <button type="button" onClick={() => removeItemRow(item.key)} className="rounded-lg p-2 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>

        <FormButton type="submit" loading={loading}>
          Create transfer
        </FormButton>
      </form>
    </Modal>
  );
}
