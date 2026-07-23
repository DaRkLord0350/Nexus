'use client';

import { useState } from 'react';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import { Modal } from '@/components/ui/modal';
import type { CustomerCreateInput } from '@/lib/customers/customers';

interface CustomerFormModalProps {
  onSubmit: (data: CustomerCreateInput) => Promise<void>;
  onClose: () => void;
}

export function CustomerFormModal({ onSubmit, onClose }: CustomerFormModalProps) {
  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phone, setPhone] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    setError(null);
    if (!email.trim() || !firstName.trim() || !lastName.trim()) {
      setError('Email, first name, and last name are required.');
      return;
    }
    setSaving(true);
    try {
      await onSubmit({ email: email.trim(), first_name: firstName.trim(), last_name: lastName.trim(), phone: phone.trim() || undefined });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create customer.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title="New customer" onClose={onClose}>
      <div className="space-y-4">
        <div>
          <FormField label="Email" htmlFor="email" />
          <FormInput id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <FormField label="First name" htmlFor="first_name" />
            <FormInput id="first_name" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
          </div>
          <div>
            <FormField label="Last name" htmlFor="last_name" />
            <FormInput id="last_name" value={lastName} onChange={(e) => setLastName(e.target.value)} />
          </div>
        </div>
        <div>
          <FormField label="Phone (optional)" htmlFor="phone" />
          <FormInput id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
        </div>
        <FormError message={error} />
        <FormButton type="button" loading={saving} onClick={handleSubmit}>
          Create customer
        </FormButton>
      </div>
    </Modal>
  );
}
