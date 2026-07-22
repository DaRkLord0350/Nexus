'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { AttributeValueCreateInput } from '@/lib/catalog/attributes';
import type { AttributeValueItem } from '@/lib/types';

interface AttributeValueFormModalProps {
  value?: AttributeValueItem | null;
  onSubmit: (data: AttributeValueCreateInput) => Promise<void>;
  onClose: () => void;
}

export function AttributeValueFormModal({ value, onSubmit, onClose }: AttributeValueFormModalProps) {
  const [text, setText] = useState(value?.value ?? '');
  const [colorHex, setColorHex] = useState(value?.color_hex ?? '');
  const [sortOrder, setSortOrder] = useState(value?.sort_order ?? 0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await onSubmit({ value: text.trim(), color_hex: colorHex.trim() || undefined, sort_order: sortOrder });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save value.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={value ? 'Edit value' : 'New value'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormError message={error} />
        <div>
          <FormField label="Value" htmlFor="value-text" />
          <FormInput id="value-text" autoFocus value={text} onChange={(e) => setText(e.target.value)} required placeholder="e.g. Red" />
        </div>
        <div>
          <FormField label="Color (optional)" htmlFor="value-color" />
          <FormInput id="value-color" type="text" placeholder="#FF0000" value={colorHex ?? ''} onChange={(e) => setColorHex(e.target.value)} />
        </div>
        <div>
          <FormField label="Sort order" htmlFor="value-sort" />
          <FormInput id="value-sort" type="number" value={sortOrder} onChange={(e) => setSortOrder(Number(e.target.value) || 0)} />
        </div>
        <FormButton type="submit" loading={loading}>
          {value ? 'Save changes' : 'Add value'}
        </FormButton>
      </form>
    </Modal>
  );
}
