'use client';

import { useState } from 'react';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import { Modal } from '@/components/ui/modal';
import type { RefundCreateInput } from '@/lib/orders/refunds';
import type { RefundMethod } from '@/lib/types';

interface RefundFormModalProps {
  onSubmit: (data: RefundCreateInput) => Promise<void>;
  onClose: () => void;
}

const METHODS: RefundMethod[] = ['original_payment', 'store_credit', 'wallet', 'bank_transfer'];

export function RefundFormModal({ onSubmit, onClose }: RefundFormModalProps) {
  const [orderId, setOrderId] = useState('');
  const [method, setMethod] = useState<RefundMethod>('original_payment');
  const [amount, setAmount] = useState('');
  const [reason, setReason] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    setError(null);
    const numericAmount = Number(amount);
    if (!orderId.trim() || !numericAmount || numericAmount <= 0) {
      setError('Order ID and a positive amount are required.');
      return;
    }
    setSaving(true);
    try {
      await onSubmit({ order_id: orderId.trim(), method, amount: numericAmount, reason: reason || undefined });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create refund.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title="New refund" onClose={onClose}>
      <div className="space-y-4">
        <div>
          <FormField label="Order ID" htmlFor="order_id" />
          <FormInput id="order_id" value={orderId} onChange={(e) => setOrderId(e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <FormField label="Method" htmlFor="method" />
            <select id="method" value={method} onChange={(e) => setMethod(e.target.value as RefundMethod)} className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
              {METHODS.map((m) => (
                <option key={m} value={m}>{m.replace(/_/g, ' ')}</option>
              ))}
            </select>
          </div>
          <div>
            <FormField label="Amount" htmlFor="amount" />
            <FormInput id="amount" type="number" min={0} step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} />
          </div>
        </div>
        <div>
          <FormField label="Reason (optional)" htmlFor="reason" />
          <FormInput id="reason" value={reason} onChange={(e) => setReason(e.target.value)} />
        </div>
        <FormError message={error} />
        <FormButton type="button" loading={saving} onClick={handleSubmit}>
          Create refund request
        </FormButton>
      </div>
    </Modal>
  );
}
