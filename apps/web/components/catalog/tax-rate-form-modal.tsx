'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { TaxRateCreateInput } from '@/lib/catalog/tax';
import type { TaxRateItem, TaxType } from '@/lib/types';

interface TaxRateFormModalProps {
  rate?: TaxRateItem | null;
  onSubmit: (data: TaxRateCreateInput) => Promise<void>;
  onClose: () => void;
}

export function TaxRateFormModal({ rate, onSubmit, onClose }: TaxRateFormModalProps) {
  const [country, setCountry] = useState(rate?.country ?? '');
  const [state, setState] = useState(rate?.state ?? '');
  const [rateValue, setRateValue] = useState(rate?.rate ?? 0);
  const [taxType, setTaxType] = useState(rate?.tax_type ?? 'gst');
  const [isInclusive, setIsInclusive] = useState(rate?.is_inclusive ?? false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!country.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        country: country.trim().toUpperCase(),
        state: state.trim() || undefined,
        rate: rateValue,
        tax_type: taxType,
        is_inclusive: isInclusive,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save tax rate.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={rate ? 'Edit tax rate' : 'New tax rate'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormError message={error} />
        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Country (ISO-2)" htmlFor="rate-country" />
            <FormInput id="rate-country" maxLength={2} value={country} onChange={(e) => setCountry(e.target.value)} required placeholder="IN" />
          </div>
          <div>
            <FormField label="State (optional)" htmlFor="rate-state" />
            <FormInput id="rate-state" value={state} onChange={(e) => setState(e.target.value)} placeholder="CA" />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Rate (%)" htmlFor="rate-value" />
            <FormInput id="rate-value" type="number" step="0.01" value={rateValue} onChange={(e) => setRateValue(Number(e.target.value) || 0)} required />
          </div>
          <div>
            <FormField label="Type" htmlFor="rate-type" />
            <select id="rate-type" value={taxType} onChange={(e) => setTaxType(e.target.value as TaxType)} className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
              <option value="gst">GST</option>
              <option value="vat">VAT</option>
              <option value="sales_tax">Sales tax</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
          <input type="checkbox" checked={isInclusive} onChange={(e) => setIsInclusive(e.target.checked)} />
          Tax-inclusive pricing
        </label>
        <FormButton type="submit" loading={loading}>
          {rate ? 'Save changes' : 'Add rate'}
        </FormButton>
      </form>
    </Modal>
  );
}
