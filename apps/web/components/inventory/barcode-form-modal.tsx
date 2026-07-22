'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { BarcodeCreateInput } from '@/lib/inventory/barcodes';
import type { BarcodeFormat } from '@/lib/types';

interface BarcodeFormModalProps {
  onSubmit: (data: BarcodeCreateInput) => Promise<void>;
  onClose: () => void;
}

export function BarcodeFormModal({ onSubmit, onClose }: BarcodeFormModalProps) {
  const [ownerType, setOwnerType] = useState<'product' | 'variant'>('product');
  const [ownerId, setOwnerId] = useState('');
  const [value, setValue] = useState('');
  const [format, setFormat] = useState<BarcodeFormat>('code128');
  const [isPrimary, setIsPrimary] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!value.trim() || !ownerId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        [ownerType === 'product' ? 'product_id' : 'variant_id']: ownerId.trim(),
        value: value.trim(),
        format,
        is_primary: isPrimary,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save barcode.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title="New barcode" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormError message={error} />

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Owner type" htmlFor="barcode-owner-type" />
            <select
              id="barcode-owner-type"
              value={ownerType}
              onChange={(e) => setOwnerType(e.target.value as 'product' | 'variant')}
              className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
            >
              <option value="product">Product</option>
              <option value="variant">Variant</option>
            </select>
          </div>
          <div>
            <FormField label={ownerType === 'product' ? 'Product ID' : 'Variant ID'} htmlFor="barcode-owner-id" />
            <FormInput id="barcode-owner-id" autoFocus value={ownerId} onChange={(e) => setOwnerId(e.target.value)} required />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Value" htmlFor="barcode-value" />
            <FormInput id="barcode-value" value={value} onChange={(e) => setValue(e.target.value)} required />
          </div>
          <div>
            <FormField label="Format" htmlFor="barcode-format" />
            <select
              id="barcode-format"
              value={format}
              onChange={(e) => setFormat(e.target.value as BarcodeFormat)}
              className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
            >
              <option value="code128">Code128</option>
              <option value="ean13">EAN13</option>
              <option value="upc">UPC</option>
              <option value="qr">QR</option>
            </select>
          </div>
        </div>

        <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
          <input type="checkbox" checked={isPrimary} onChange={(e) => setIsPrimary(e.target.checked)} />
          Primary barcode for this item
        </label>

        <FormButton type="submit" loading={loading}>
          Create barcode
        </FormButton>
      </form>
    </Modal>
  );
}
