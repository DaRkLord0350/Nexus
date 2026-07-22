'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { AttributeCreateInput } from '@/lib/catalog/attributes';
import type { AttributeInputType, AttributeItem } from '@/lib/types';

interface AttributeFormModalProps {
  attribute?: AttributeItem | null;
  onSubmit: (data: AttributeCreateInput) => Promise<void>;
  onClose: () => void;
}

export function AttributeFormModal({ attribute, onSubmit, onClose }: AttributeFormModalProps) {
  const [name, setName] = useState(attribute?.name ?? '');
  const [code, setCode] = useState(attribute?.code ?? '');
  const [inputType, setInputType] = useState(attribute?.input_type ?? 'select');
  const [isVariantAttribute, setIsVariantAttribute] = useState(attribute?.is_variant_attribute ?? true);
  const [isActive, setIsActive] = useState(attribute?.is_active ?? true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        name: name.trim(),
        code: code.trim() || undefined,
        input_type: inputType,
        is_variant_attribute: isVariantAttribute,
        is_active: isActive,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save attribute.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={attribute ? 'Edit attribute' : 'New attribute'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormError message={error} />

        <div>
          <FormField label="Name" htmlFor="attr-name" />
          <FormInput id="attr-name" autoFocus value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g. Color" />
        </div>

        <div>
          <FormField label="Code (optional)" htmlFor="attr-code" />
          <FormInput id="attr-code" placeholder="auto-generated from name" value={code} onChange={(e) => setCode(e.target.value)} />
        </div>

        <div>
          <FormField label="Input type" htmlFor="attr-type" />
          <select
            id="attr-type"
            value={inputType}
            onChange={(e) => setInputType(e.target.value as AttributeInputType)}
            className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
          >
            <option value="select">Select (predefined values)</option>
            <option value="text">Text</option>
            <option value="number">Number</option>
            <option value="boolean">Boolean</option>
          </select>
        </div>

        <div className="flex gap-6">
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input type="checkbox" checked={isVariantAttribute} onChange={(e) => setIsVariantAttribute(e.target.checked)} />
            Used for variants
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
            Active
          </label>
        </div>

        <FormButton type="submit" loading={loading}>
          {attribute ? 'Save changes' : 'Create attribute'}
        </FormButton>
      </form>
    </Modal>
  );
}
