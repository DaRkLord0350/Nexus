'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { BatchCreateInput, BatchUpdateInput } from '@/lib/inventory/batches';
import type { BatchItem, BatchStatus } from '@/lib/types';

interface BatchFormModalProps {
  batch?: BatchItem | null;
  onSubmit: (data: BatchCreateInput | BatchUpdateInput) => Promise<void>;
  onClose: () => void;
}

function toDateInput(value?: string | null): string {
  if (!value) return '';
  return value.slice(0, 10);
}

export function BatchFormModal({ batch, onSubmit, onClose }: BatchFormModalProps) {
  const [productId, setProductId] = useState(batch?.product_id ?? '');
  const [warehouseId, setWarehouseId] = useState(batch?.warehouse_id ?? '');
  const [batchNumber, setBatchNumber] = useState(batch?.batch_number ?? '');
  const [manufacturedDate, setManufacturedDate] = useState(toDateInput(batch?.manufactured_date));
  const [expiryDate, setExpiryDate] = useState(toDateInput(batch?.expiry_date));
  const [receivedQuantity, setReceivedQuantity] = useState(batch ? String(batch.received_quantity) : '0');
  const [remainingQuantity, setRemainingQuantity] = useState(batch ? String(batch.remaining_quantity) : '');
  const [costPrice, setCostPrice] = useState(batch?.cost_price != null ? String(batch.cost_price) : '');
  const [statusValue, setStatusValue] = useState<BatchStatus>(batch?.status ?? 'active');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!batch && (!productId.trim() || !warehouseId.trim() || !batchNumber.trim())) return;
    setLoading(true);
    setError(null);
    try {
      if (batch) {
        await onSubmit({
          manufactured_date: manufacturedDate || undefined,
          expiry_date: expiryDate || undefined,
          remaining_quantity: remainingQuantity ? Number(remainingQuantity) : undefined,
          cost_price: costPrice ? Number(costPrice) : undefined,
          status: statusValue,
        });
      } else {
        await onSubmit({
          product_id: productId.trim(),
          warehouse_id: warehouseId.trim(),
          batch_number: batchNumber.trim(),
          manufactured_date: manufacturedDate || undefined,
          expiry_date: expiryDate || undefined,
          received_quantity: receivedQuantity ? Number(receivedQuantity) : 0,
          cost_price: costPrice ? Number(costPrice) : undefined,
          status: statusValue,
        });
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save batch.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={batch ? 'Edit batch' : 'New batch'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="max-h-[70vh] space-y-4 overflow-y-auto pr-1">
        <FormError message={error} />

        {!batch ? (
          <>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <FormField label="Product ID" htmlFor="batch-product" />
                <FormInput id="batch-product" autoFocus value={productId} onChange={(e) => setProductId(e.target.value)} required />
              </div>
              <div>
                <FormField label="Warehouse ID" htmlFor="batch-warehouse" />
                <FormInput id="batch-warehouse" value={warehouseId} onChange={(e) => setWarehouseId(e.target.value)} required />
              </div>
            </div>
            <div>
              <FormField label="Batch number" htmlFor="batch-number" />
              <FormInput id="batch-number" value={batchNumber} onChange={(e) => setBatchNumber(e.target.value)} required />
            </div>
            <div>
              <FormField label="Received quantity" htmlFor="batch-received" />
              <FormInput id="batch-received" type="number" min={0} value={receivedQuantity} onChange={(e) => setReceivedQuantity(e.target.value)} />
            </div>
          </>
        ) : (
          <div>
            <FormField label="Remaining quantity" htmlFor="batch-remaining" />
            <FormInput id="batch-remaining" type="number" min={0} value={remainingQuantity} onChange={(e) => setRemainingQuantity(e.target.value)} />
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Manufactured date" htmlFor="batch-mfg-date" />
            <FormInput id="batch-mfg-date" type="date" value={manufacturedDate} onChange={(e) => setManufacturedDate(e.target.value)} />
          </div>
          <div>
            <FormField label="Expiry date" htmlFor="batch-expiry-date" />
            <FormInput id="batch-expiry-date" type="date" value={expiryDate} onChange={(e) => setExpiryDate(e.target.value)} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Cost price" htmlFor="batch-cost" />
            <FormInput id="batch-cost" type="number" step="0.01" min={0} value={costPrice} onChange={(e) => setCostPrice(e.target.value)} />
          </div>
          <div>
            <FormField label="Status" htmlFor="batch-status" />
            <select
              id="batch-status"
              value={statusValue}
              onChange={(e) => setStatusValue(e.target.value as BatchStatus)}
              className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
            >
              <option value="active">Active</option>
              <option value="depleted">Depleted</option>
              <option value="expired">Expired</option>
              <option value="quarantined">Quarantined</option>
              <option value="recalled">Recalled</option>
            </select>
          </div>
        </div>

        <FormButton type="submit" loading={loading}>
          {batch ? 'Save changes' : 'Create batch'}
        </FormButton>
      </form>
    </Modal>
  );
}
