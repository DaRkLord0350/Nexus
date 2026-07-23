'use client';

import { useState } from 'react';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import { Modal } from '@/components/ui/modal';
import type { PickupCreateInput } from '@/lib/shipping/pickups';

interface PickupFormModalProps {
  onSubmit: (data: PickupCreateInput) => Promise<void>;
  onClose: () => void;
}

export function PickupFormModal({ onSubmit, onClose }: PickupFormModalProps) {
  const [warehouseId, setWarehouseId] = useState('');
  const [scheduledDate, setScheduledDate] = useState('');
  const [timeSlot, setTimeSlot] = useState('');
  const [shipmentIds, setShipmentIds] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    setError(null);
    if (!warehouseId.trim() || !scheduledDate) {
      setError('Warehouse ID and scheduled date are required.');
      return;
    }
    setSaving(true);
    try {
      await onSubmit({
        warehouse_id: warehouseId.trim(),
        scheduled_date: new Date(scheduledDate).toISOString(),
        time_slot: timeSlot || undefined,
        shipment_ids: shipmentIds.trim() ? shipmentIds.split(',').map((s) => s.trim()).filter(Boolean) : undefined,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to schedule pickup.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title="Schedule pickup" onClose={onClose}>
      <div className="space-y-4">
        <div>
          <FormField label="Warehouse ID" htmlFor="warehouse_id" />
          <FormInput id="warehouse_id" value={warehouseId} onChange={(e) => setWarehouseId(e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <FormField label="Scheduled date" htmlFor="scheduled_date" />
            <FormInput id="scheduled_date" type="datetime-local" value={scheduledDate} onChange={(e) => setScheduledDate(e.target.value)} />
          </div>
          <div>
            <FormField label="Time slot (optional)" htmlFor="time_slot" />
            <FormInput id="time_slot" value={timeSlot} onChange={(e) => setTimeSlot(e.target.value)} placeholder="e.g. 10:00-14:00" />
          </div>
        </div>
        <div>
          <FormField label="Shipment IDs (comma-separated, optional)" htmlFor="shipment_ids" />
          <FormInput id="shipment_ids" value={shipmentIds} onChange={(e) => setShipmentIds(e.target.value)} />
        </div>
        <FormError message={error} />
        <FormButton type="button" loading={saving} onClick={handleSubmit}>
          Schedule pickup
        </FormButton>
      </div>
    </Modal>
  );
}
