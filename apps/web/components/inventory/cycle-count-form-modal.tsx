'use client';

import { Plus, Trash2 } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { CycleCountCreateInput, CycleCountItemInput } from '@/lib/inventory/cycle-counts';
import type { WarehouseItem } from '@/lib/types';

interface CycleCountFormModalProps {
  warehouses: WarehouseItem[];
  onSubmit: (data: CycleCountCreateInput) => Promise<void>;
  onClose: () => void;
}

interface DraftItem extends CycleCountItemInput {
  key: string;
}

export function CycleCountFormModal({ warehouses, onSubmit, onClose }: CycleCountFormModalProps) {
  const [warehouseId, setWarehouseId] = useState(warehouses[0]?.id ?? '');
  const [scheduledDate, setScheduledDate] = useState('');
  const [notes, setNotes] = useState('');
  const [items, setItems] = useState<DraftItem[]>([{ key: crypto.randomUUID(), product_id: '' }]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addItemRow = () => {
    setItems((prev) => [...prev, { key: crypto.randomUUID(), product_id: '' }]);
  };

  const removeItemRow = (key: string) => {
    setItems((prev) => prev.filter((item) => item.key !== key));
  };

  const updateItem = (key: string, patch: Partial<DraftItem>) => {
    setItems((prev) => prev.map((item) => (item.key === key ? { ...item, ...patch } : item)));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!warehouseId) return;
    setLoading(true);
    setError(null);
    try {
      const validItems = items.filter((item) => item.product_id.trim());
      await onSubmit({
        warehouse_id: warehouseId,
        scheduled_date: scheduledDate || undefined,
        notes: notes.trim() || undefined,
        items: validItems.map(({ key, ...rest }) => rest),
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create cycle count.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title="New cycle count" onClose={onClose}>
      <form onSubmit={handleSubmit} className="max-h-[75vh] space-y-4 overflow-y-auto pr-1">
        <FormError message={error} />

        <div>
          <FormField label="Warehouse" htmlFor="cc-warehouse" />
          <select
            id="cc-warehouse"
            value={warehouseId}
            onChange={(e) => setWarehouseId(e.target.value)}
            required
            className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
          >
            <option value="">Select warehouse…</option>
            {warehouses.map((w) => (
              <option key={w.id} value={w.id}>{w.name}</option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Scheduled date" htmlFor="cc-date" />
            <FormInput id="cc-date" type="date" value={scheduledDate} onChange={(e) => setScheduledDate(e.target.value)} />
          </div>
          <div>
            <FormField label="Notes" htmlFor="cc-notes" />
            <FormInput id="cc-notes" value={notes} onChange={(e) => setNotes(e.target.value)} />
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <FormField label="Products to count" htmlFor="cc-items" />
            <button type="button" onClick={addItemRow} className="flex items-center gap-1 text-xs font-semibold text-cyan-600 dark:text-cyan-400">
              <Plus size={12} /> Add product
            </button>
          </div>
          {items.map((item) => (
            <div key={item.key} className="grid grid-cols-[1fr_auto] gap-2">
              <FormInput placeholder="Product ID" value={item.product_id} onChange={(e) => updateItem(item.key, { product_id: e.target.value })} />
              <button type="button" onClick={() => removeItemRow(item.key)} className="rounded-lg p-2 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>

        <FormButton type="submit" loading={loading}>
          Create cycle count
        </FormButton>
      </form>
    </Modal>
  );
}
