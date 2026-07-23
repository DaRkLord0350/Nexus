'use client';

import { useState } from 'react';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import { Modal } from '@/components/ui/modal';
import type { ShippingProviderCreateInput } from '@/lib/shipping/providers';

interface ProviderFormModalProps {
  onSubmit: (data: ShippingProviderCreateInput) => Promise<void>;
  onClose: () => void;
}

const PROVIDER_TYPES = ['manual', 'shiprocket', 'delhivery', 'bluedart', 'fedex', 'dhl', 'aramex', 'ups', 'other'];

export function ProviderFormModal({ onSubmit, onClose }: ProviderFormModalProps) {
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [providerType, setProviderType] = useState('manual');
  const [baseRate, setBaseRate] = useState('');
  const [baseTransitDays, setBaseTransitDays] = useState('');
  const [supportsCod, setSupportsCod] = useState(true);
  const [isDefault, setIsDefault] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    setError(null);
    if (!name.trim() || !code.trim()) {
      setError('Name and code are required.');
      return;
    }
    setSaving(true);
    try {
      await onSubmit({
        name: name.trim(),
        code: code.trim(),
        provider_type: providerType,
        base_rate: baseRate ? Number(baseRate) : undefined,
        base_transit_days: baseTransitDays ? Number(baseTransitDays) : undefined,
        supports_cod: supportsCod,
        is_default: isDefault,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create shipping provider.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title="New shipping provider" onClose={onClose}>
      <div className="space-y-4">
        <div>
          <FormField label="Name" htmlFor="name" />
          <FormInput id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Shiprocket Main" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <FormField label="Code" htmlFor="code" />
            <FormInput id="code" value={code} onChange={(e) => setCode(e.target.value)} placeholder="e.g. shiprocket-main" />
          </div>
          <div>
            <FormField label="Provider type" htmlFor="provider_type" />
            <select id="provider_type" value={providerType} onChange={(e) => setProviderType(e.target.value)} className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
              {PROVIDER_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <FormField label="Base rate (fallback)" htmlFor="base_rate" />
            <FormInput id="base_rate" type="number" min={0} step="0.01" value={baseRate} onChange={(e) => setBaseRate(e.target.value)} />
          </div>
          <div>
            <FormField label="Base transit days" htmlFor="base_transit_days" />
            <FormInput id="base_transit_days" type="number" min={0} value={baseTransitDays} onChange={(e) => setBaseTransitDays(e.target.value)} />
          </div>
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
          <input type="checkbox" checked={supportsCod} onChange={(e) => setSupportsCod(e.target.checked)} />
          Supports cash on delivery
        </label>
        <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
          <input type="checkbox" checked={isDefault} onChange={(e) => setIsDefault(e.target.checked)} />
          Set as default provider
        </label>
        <FormError message={error} />
        <FormButton type="button" loading={saving} onClick={handleSubmit}>
          Create provider
        </FormButton>
      </div>
    </Modal>
  );
}
