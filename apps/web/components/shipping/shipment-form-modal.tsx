'use client';

import { useState } from 'react';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import { Modal } from '@/components/ui/modal';
import type { ShipmentCreateInput } from '@/lib/shipping/shipments';

interface ShipmentFormModalProps {
  onSubmit: (data: ShipmentCreateInput) => Promise<void>;
  onClose: () => void;
}

export function ShipmentFormModal({ onSubmit, onClose }: ShipmentFormModalProps) {
  const [orderId, setOrderId] = useState('');
  const [orderItemId, setOrderItemId] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [warehouseId, setWarehouseId] = useState('');
  const [providerId, setProviderId] = useState('');
  const [weight, setWeight] = useState('');
  const [isCod, setIsCod] = useState(false);
  const [codAmount, setCodAmount] = useState('');
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
        warehouse_id: warehouseId.trim() || undefined,
        shipping_provider_id: providerId.trim() || undefined,
        items: [{ order_item_id: orderItemId.trim(), quantity: Number(quantity) || 1 }],
        weight: weight ? Number(weight) : undefined,
        is_cod: isCod,
        cod_amount: isCod && codAmount ? Number(codAmount) : undefined,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create shipment.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title="New shipment" onClose={onClose}>
      <div className="space-y-4">
        <div>
          <FormField label="Order ID" htmlFor="order_id" />
          <FormInput id="order_id" value={orderId} onChange={(e) => setOrderId(e.target.value)} />
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
        <div className="grid grid-cols-2 gap-3">
          <div>
            <FormField label="Warehouse ID (optional, auto-allocated)" htmlFor="warehouse_id" />
            <FormInput id="warehouse_id" value={warehouseId} onChange={(e) => setWarehouseId(e.target.value)} placeholder="Auto" />
          </div>
          <div>
            <FormField label="Provider ID (optional, auto-selected)" htmlFor="provider_id" />
            <FormInput id="provider_id" value={providerId} onChange={(e) => setProviderId(e.target.value)} placeholder="Auto" />
          </div>
        </div>
        <div>
          <FormField label="Weight (kg, optional)" htmlFor="weight" />
          <FormInput id="weight" type="number" min={0} step="0.1" value={weight} onChange={(e) => setWeight(e.target.value)} />
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
          <input type="checkbox" checked={isCod} onChange={(e) => setIsCod(e.target.checked)} />
          Cash on delivery
        </label>
        {isCod ? (
          <div>
            <FormField label="COD amount" htmlFor="cod_amount" />
            <FormInput id="cod_amount" type="number" min={0} step="0.01" value={codAmount} onChange={(e) => setCodAmount(e.target.value)} />
          </div>
        ) : null}
        <FormError message={error} />
        <FormButton type="button" loading={saving} onClick={handleSubmit}>
          Create shipment
        </FormButton>
      </div>
    </Modal>
  );
}
