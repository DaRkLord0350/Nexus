'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { TagCreateInput } from '@/lib/catalog/tags';
import type { TagItem } from '@/lib/types';

interface TagFormModalProps {
  tag?: TagItem | null;
  onSubmit: (data: TagCreateInput) => Promise<void>;
  onClose: () => void;
}

export function TagFormModal({ tag, onSubmit, onClose }: TagFormModalProps) {
  const [name, setName] = useState(tag?.name ?? '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await onSubmit({ name: name.trim() });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save tag.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={tag ? 'Edit tag' : 'New tag'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormError message={error} />
        <div>
          <FormField label="Name" htmlFor="tag-name" />
          <FormInput id="tag-name" autoFocus value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g. Best Seller" />
        </div>
        <FormButton type="submit" loading={loading}>
          {tag ? 'Save changes' : 'Create tag'}
        </FormButton>
      </form>
    </Modal>
  );
}
