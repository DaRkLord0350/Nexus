'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { SerialNumberCreateInput, SerialNumberImportInput } from '@/lib/inventory/serial-numbers';

interface SerialNumberFormModalProps {
  onSubmit: (data: SerialNumberCreateInput) => Promise<void>;
  onImport: (data: SerialNumberImportInput) => Promise<{ imported_count: number; skipped: string[] }>;
  onClose: () => void;
}

export function SerialNumberFormModal({ onSubmit, onImport, onClose }: SerialNumberFormModalProps) {
  const [mode, setMode] = useState<'single' | 'import'>('single');
  const [productId, setProductId] = useState('');
  const [warehouseId, setWarehouseId] = useState('');
  const [serial, setSerial] = useState('');
  const [serialsBulk, setSerialsBulk] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [importResult, setImportResult] = useState<{ imported_count: number; skipped: string[] } | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!productId.trim() || !warehouseId.trim()) return;
    setLoading(true);
    setError(null);
    setImportResult(null);
    try {
      if (mode === 'single') {
        if (!serial.trim()) return;
        await onSubmit({ product_id: productId.trim(), warehouse_id: warehouseId.trim(), serial: serial.trim() });
        onClose();
      } else {
        const serials = serialsBulk.split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
        if (serials.length === 0) return;
        const result = await onImport({ product_id: productId.trim(), warehouse_id: warehouseId.trim(), serials });
        setImportResult(result);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save serial number(s).');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title="Add serial numbers" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormError message={error} />
        {importResult ? (
          <div className="rounded-xl border border-emerald-300 bg-emerald-50 px-3.5 py-2.5 text-sm text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300">
            Imported {importResult.imported_count} serial(s).
            {importResult.skipped.length > 0 ? ` Skipped ${importResult.skipped.length} duplicate(s): ${importResult.skipped.join(', ')}` : ''}
          </div>
        ) : null}

        <div className="flex gap-2 rounded-xl border border-slate-200 p-1 dark:border-slate-800">
          <button
            type="button"
            onClick={() => setMode('single')}
            className={`flex-1 rounded-lg py-1.5 text-sm font-medium transition ${mode === 'single' ? 'bg-cyan-500 text-slate-950' : 'text-slate-600 dark:text-slate-300'}`}
          >
            Single
          </button>
          <button
            type="button"
            onClick={() => setMode('import')}
            className={`flex-1 rounded-lg py-1.5 text-sm font-medium transition ${mode === 'import' ? 'bg-cyan-500 text-slate-950' : 'text-slate-600 dark:text-slate-300'}`}
          >
            Bulk import
          </button>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Product ID" htmlFor="serial-product" />
            <FormInput id="serial-product" autoFocus value={productId} onChange={(e) => setProductId(e.target.value)} required />
          </div>
          <div>
            <FormField label="Warehouse ID" htmlFor="serial-warehouse" />
            <FormInput id="serial-warehouse" value={warehouseId} onChange={(e) => setWarehouseId(e.target.value)} required />
          </div>
        </div>

        {mode === 'single' ? (
          <div>
            <FormField label="Serial" htmlFor="serial-value" />
            <FormInput id="serial-value" value={serial} onChange={(e) => setSerial(e.target.value)} required />
          </div>
        ) : (
          <div>
            <FormField label="Serials (one per line)" htmlFor="serial-bulk" />
            <textarea
              id="serial-bulk"
              rows={6}
              value={serialsBulk}
              onChange={(e) => setSerialsBulk(e.target.value)}
              className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
            />
          </div>
        )}

        <FormButton type="submit" loading={loading}>
          {mode === 'single' ? 'Create serial' : 'Import serials'}
        </FormButton>
      </form>
    </Modal>
  );
}
