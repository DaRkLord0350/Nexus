'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { CustomFieldDefinitionCreateInput } from '@/lib/catalog/custom-fields';
import type { CustomFieldDefinitionItem, CustomFieldEntityType, CustomFieldType } from '@/lib/types';

interface CustomFieldDefinitionFormModalProps {
  entityType: CustomFieldEntityType;
  definition?: CustomFieldDefinitionItem | null;
  onSubmit: (data: CustomFieldDefinitionCreateInput) => Promise<void>;
  onClose: () => void;
}

export function CustomFieldDefinitionFormModal({ entityType, definition, onSubmit, onClose }: CustomFieldDefinitionFormModalProps) {
  const [name, setName] = useState(definition?.name ?? '');
  const [fieldType, setFieldType] = useState(definition?.field_type ?? 'text');
  const [options, setOptions] = useState((definition?.options ?? []).join(', '));
  const [isRequired, setIsRequired] = useState(definition?.is_required ?? false);
  const [isActive, setIsActive] = useState(definition?.is_active ?? true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        entity_type: entityType,
        name: name.trim(),
        field_type: fieldType,
        options: fieldType === 'select' ? options.split(',').map((o) => o.trim()).filter(Boolean) : undefined,
        is_required: isRequired,
        is_active: isActive,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save custom field.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={definition ? 'Edit custom field' : 'New custom field'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormError message={error} />
        <div>
          <FormField label="Name" htmlFor="cf-name" />
          <FormInput id="cf-name" autoFocus value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g. Care Instructions" />
        </div>
        <div>
          <FormField label="Type" htmlFor="cf-type" />
          <select
            id="cf-type"
            value={fieldType}
            onChange={(e) => setFieldType(e.target.value as CustomFieldType)}
            disabled={!!definition}
            className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 disabled:opacity-60 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
          >
            <option value="text">Text</option>
            <option value="number">Number</option>
            <option value="boolean">Boolean</option>
            <option value="date">Date</option>
            <option value="select">Select</option>
            <option value="json">JSON</option>
          </select>
        </div>
        {fieldType === 'select' ? (
          <div>
            <FormField label="Options (comma-separated)" htmlFor="cf-options" />
            <FormInput id="cf-options" value={options} onChange={(e) => setOptions(e.target.value)} placeholder="Small, Medium, Large" />
          </div>
        ) : null}
        <div className="flex gap-6">
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input type="checkbox" checked={isRequired} onChange={(e) => setIsRequired(e.target.checked)} />
            Required
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
            Active
          </label>
        </div>
        <FormButton type="submit" loading={loading}>
          {definition ? 'Save changes' : 'Create custom field'}
        </FormButton>
      </form>
    </Modal>
  );
}
