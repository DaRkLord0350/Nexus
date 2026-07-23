'use client';

import { useState } from 'react';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import { Modal } from '@/components/ui/modal';
import type { ReturnCreateInput } from '@/lib/orders/returns';

interface ReturnFormModalProps {
  onSubmit: (data: ReturnCreateInput) => Promise<void>;
  onClose: () => void;
}

const REASON_CODES = ['damaged', 'wrong_item', 'not_as_described', 'no_longer_needed', 'defective', 'other'];

export function ReturnFormModal({ onSubmit, onClose }: ReturnFormModalProps) {
  const [orderId, setOrderId] = useState('');
  const [orderItemId, setOrderItemId] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [reasonCode, setReasonCode] = useState('damaged');
  const [reasonNotes, setReasonNotes] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    setError(null);
    if (!orderId.trim() || !orderItemId.trim()) {
      setError('Order ID and order item ID are required.');
      return;
    }
    setSaving(true);
    try {
      await onSubmit({
        order_id: orderId.trim(),
        reason_code: reasonCode,
        reason_notes: reasonNotes || undefined,
        items: [{ order_item_id: orderItemId.trim(), quantity: Number(quantity) || 1 }],
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create return request.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title="New return request" onClose={onClose}>
      <div className="space-y-4">
        <div>
          <FormField label="Order ID" htmlFor="order_id" />
          <FormInput id="order_id" value={orderId} onChange={(e) => setOrderId(e.target.value)} placeholder="Only delivered orders are eligible" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <FormField label="Order item ID" htmlFor="order_item_id" />
            <FormInput id="order_item_id" value={orderItemId} onChange={(e) => setOrderItemId(e.target.value)} />
          </div>
          <div>
            <FormField label="Quantity" htmlFor="quantity" />
            <FormInput id="quantity" type="number" min={1} value={quantity} onChange={(e) => setQuantity(e.target.value)} />
          </div>
        </div>
        <div>
          <FormField label="Reason" htmlFor="reason_code" />
          <select id="reason_code" value={reasonCode} onChange={(e) => setReasonCode(e.target.value)} className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
            {REASON_CODES.map((code) => (
              <option key={code} value={code}>{code.replace(/_/g, ' ')}</option>
            ))}
          </select>
        </div>
        <div>
          <FormField label="Notes (optional)" htmlFor="reason_notes" />
          <FormInput id="reason_notes" value={reasonNotes} onChange={(e) => setReasonNotes(e.target.value)} />
        </div>
        <FormError message={error} />
        <FormButton type="button" loading={saving} onClick={handleSubmit}>
          Create return request
        </FormButton>
      </div>
    </Modal>
  );
}
