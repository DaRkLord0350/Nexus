'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { StockAdjustmentCreateInput } from '@/lib/inventory/adjustments';
import type { StockAdjustmentReason } from '@/lib/types';

interface StockAdjustmentFormModalProps {
  onSubmit: (data: StockAdjustmentCreateInput) => Promise<void>;
  onClose: () => void;
}

export function StockAdjustmentFormModal({ onSubmit, onClose }: StockAdjustmentFormModalProps) {
  const [productId, setProductId] = useState('');
  const [warehouseId, setWarehouseId] = useState('');
  const [quantityDelta, setQuantityDelta] = useState('');
  const [reason, setReason] = useState<StockAdjustmentReason>('manual');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!productId.trim() || !warehouseId.trim() || !quantityDelta) return;
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        product_id: productId.trim(),
        warehouse_id: warehouseId.trim(),
        quantity_delta: Number(quantityDelta),
        reason,
        notes: notes.trim() || undefined,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create stock adjustment.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title="New stock adjustment" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormError message={error} />

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Product ID" htmlFor="adj-product" />
            <FormInput id="adj-product" autoFocus value={productId} onChange={(e) => setProductId(e.target.value)} required />
          </div>
          <div>
            <FormField label="Warehouse ID" htmlFor="adj-warehouse" />
            <FormInput id="adj-warehouse" value={warehouseId} onChange={(e) => setWarehouseId(e.target.value)} required />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Quantity delta (+/-)" htmlFor="adj-qty" />
            <FormInput id="adj-qty" type="number" value={quantityDelta} onChange={(e) => setQuantityDelta(e.target.value)} required placeholder="e.g. -5 or 10" />
          </div>
          <div>
            <FormField label="Reason" htmlFor="adj-reason" />
            <select
              id="adj-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value as StockAdjustmentReason)}
              className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
            >
              <option value="manual">Manual</option>
              <option value="damage">Damage</option>
              <option value="lost">Lost</option>
              <option value="found">Found</option>
              <option value="audit">Audit</option>
            </select>
          </div>
        </div>

        <div>
          <FormField label="Notes" htmlFor="adj-notes" />
          <FormInput id="adj-notes" value={notes} onChange={(e) => setNotes(e.target.value)} />
        </div>

        <FormButton type="submit" loading={loading}>
          Create adjustment
        </FormButton>
      </form>
    </Modal>
  );
}
