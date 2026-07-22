'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { TaxClassCreateInput } from '@/lib/catalog/tax';
import type { TaxClassItem } from '@/lib/types';

interface TaxClassFormModalProps {
  taxClass?: TaxClassItem | null;
  onSubmit: (data: TaxClassCreateInput) => Promise<void>;
  onClose: () => void;
}

export function TaxClassFormModal({ taxClass, onSubmit, onClose }: TaxClassFormModalProps) {
  const [name, setName] = useState(taxClass?.name ?? '');
  const [code, setCode] = useState(taxClass?.code ?? '');
  const [description, setDescription] = useState(taxClass?.description ?? '');
  const [isDefault, setIsDefault] = useState(taxClass?.is_default ?? false);
  const [isActive, setIsActive] = useState(taxClass?.is_active ?? true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await onSubmit({ name: name.trim(), code: code.trim() || undefined, description: description.trim() || undefined, is_default: isDefault, is_active: isActive });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save tax class.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={taxClass ? 'Edit tax class' : 'New tax class'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormError message={error} />
        <div>
          <FormField label="Name" htmlFor="tax-name" />
          <FormInput id="tax-name" autoFocus value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g. Standard GST" />
        </div>
        <div>
          <FormField label="Code (optional)" htmlFor="tax-code" />
          <FormInput id="tax-code" placeholder="auto-generated from name" value={code} onChange={(e) => setCode(e.target.value)} />
        </div>
        <div>
          <FormField label="Description" htmlFor="tax-description" />
          <FormInput id="tax-description" value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>
        <div className="flex gap-6">
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input type="checkbox" checked={isDefault} onChange={(e) => setIsDefault(e.target.checked)} />
            Default tax class
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
            Active
          </label>
        </div>
        <FormButton type="submit" loading={loading}>
          {taxClass ? 'Save changes' : 'Create tax class'}
        </FormButton>
      </form>
    </Modal>
  );
}
