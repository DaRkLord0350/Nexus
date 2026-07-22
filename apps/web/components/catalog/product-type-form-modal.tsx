'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { ProductTypeCreateInput } from '@/lib/catalog/product-types';
import type { ProductTypeItem } from '@/lib/types';

interface ProductTypeFormModalProps {
  productType?: ProductTypeItem | null;
  onSubmit: (data: ProductTypeCreateInput) => Promise<void>;
  onClose: () => void;
}

export function ProductTypeFormModal({ productType, onSubmit, onClose }: ProductTypeFormModalProps) {
  const [name, setName] = useState(productType?.name ?? '');
  const [description, setDescription] = useState(productType?.description ?? '');
  const [isActive, setIsActive] = useState(productType?.is_active ?? true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await onSubmit({ name: name.trim(), description: description.trim() || undefined, is_active: isActive });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save product type.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={productType ? 'Edit product type' : 'New product type'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormError message={error} />
        <div>
          <FormField label="Name" htmlFor="pt-name" />
          <FormInput id="pt-name" autoFocus value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g. T-Shirt" />
        </div>
        <div>
          <FormField label="Description" htmlFor="pt-description" />
          <FormInput id="pt-description" value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
          <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
          Active
        </label>
        <FormButton type="submit" loading={loading}>
          {productType ? 'Save changes' : 'Create product type'}
        </FormButton>
      </form>
    </Modal>
  );
}
