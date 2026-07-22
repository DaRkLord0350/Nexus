'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { InventoryUpdateInput } from '@/lib/inventory/stock';
import type { InventoryItem } from '@/lib/types';

interface InventoryEditModalProps {
  inventory: InventoryItem;
  onSubmit: (data: InventoryUpdateInput) => Promise<void>;
  onClose: () => void;
}

export function InventoryEditModal({ inventory, onSubmit, onClose }: InventoryEditModalProps) {
  const [minimumStock, setMinimumStock] = useState(inventory.minimum_stock != null ? String(inventory.minimum_stock) : '');
  const [maximumStock, setMaximumStock] = useState(inventory.maximum_stock != null ? String(inventory.maximum_stock) : '');
  const [reorderPoint, setReorderPoint] = useState(inventory.reorder_point != null ? String(inventory.reorder_point) : '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        minimum_stock: minimumStock ? Number(minimumStock) : undefined,
        maximum_stock: maximumStock ? Number(maximumStock) : undefined,
        reorder_point: reorderPoint ? Number(reorderPoint) : undefined,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update stock configuration.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title="Edit stock configuration" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormError message={error} />

        <div className="rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-950/60 dark:text-slate-300">
          Available: <span className="font-semibold text-slate-900 dark:text-white">{inventory.quantity_available}</span>
          {' · '}Reserved: {inventory.quantity_reserved}
          {' · '}Incoming: {inventory.quantity_incoming}
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <FormField label="Min stock" htmlFor="inv-min" />
            <FormInput id="inv-min" type="number" min={0} value={minimumStock} onChange={(e) => setMinimumStock(e.target.value)} />
          </div>
          <div>
            <FormField label="Max stock" htmlFor="inv-max" />
            <FormInput id="inv-max" type="number" min={0} value={maximumStock} onChange={(e) => setMaximumStock(e.target.value)} />
          </div>
          <div>
            <FormField label="Reorder point" htmlFor="inv-reorder" />
            <FormInput id="inv-reorder" type="number" min={0} value={reorderPoint} onChange={(e) => setReorderPoint(e.target.value)} />
          </div>
        </div>

        <FormButton type="submit" loading={loading}>
          Save changes
        </FormButton>
      </form>
    </Modal>
  );
}
