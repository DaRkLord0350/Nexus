'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormInput } from '@/components/ui/form';

interface NamePromptModalProps {
  title: string;
  initialValue?: string;
  submitLabel?: string;
  onSubmit: (value: string) => Promise<void>;
  onClose: () => void;
}

export function NamePromptModal({ title, initialValue = '', submitLabel = 'Save', onSubmit, onClose }: NamePromptModalProps) {
  const [value, setValue] = useState(initialValue);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!value.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await onSubmit(value.trim());
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={title} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormError message={error} />
        <FormInput autoFocus value={value} onChange={(e) => setValue(e.target.value)} />
        <FormButton type="submit" loading={loading}>
          {submitLabel}
        </FormButton>
      </form>
    </Modal>
  );
}
