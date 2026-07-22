'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { WarehouseZoneCreateInput } from '@/lib/inventory/warehouses';
import type { WarehouseZoneItem, WarehouseZoneType } from '@/lib/types';

interface WarehouseZoneFormModalProps {
  zone?: WarehouseZoneItem | null;
  onSubmit: (data: WarehouseZoneCreateInput) => Promise<void>;
  onClose: () => void;
}

export function WarehouseZoneFormModal({ zone, onSubmit, onClose }: WarehouseZoneFormModalProps) {
  const [name, setName] = useState(zone?.name ?? '');
  const [code, setCode] = useState(zone?.code ?? '');
  const [zoneType, setZoneType] = useState<WarehouseZoneType>(zone?.zone_type ?? 'storage');
  const [description, setDescription] = useState(zone?.description ?? '');
  const [isActive, setIsActive] = useState(zone?.is_active ?? true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim() || !code.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        name: name.trim(),
        code: code.trim(),
        zone_type: zoneType,
        description: description.trim() || undefined,
        is_active: isActive,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save zone.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={zone ? 'Edit zone' : 'New zone'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormError message={error} />

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Name" htmlFor="zone-name" />
            <FormInput id="zone-name" autoFocus value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div>
            <FormField label="Code" htmlFor="zone-code" />
            <FormInput id="zone-code" value={code} onChange={(e) => setCode(e.target.value)} required />
          </div>
        </div>

        <div>
          <FormField label="Type" htmlFor="zone-type" />
          <select
            id="zone-type"
            value={zoneType}
            onChange={(e) => setZoneType(e.target.value as WarehouseZoneType)}
            className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
          >
            <option value="receiving">Receiving</option>
            <option value="storage">Storage</option>
            <option value="picking">Picking</option>
            <option value="packing">Packing</option>
            <option value="returns">Returns</option>
            <option value="damaged">Damaged</option>
          </select>
        </div>

        <div>
          <FormField label="Description" htmlFor="zone-description" />
          <FormInput id="zone-description" value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>

        <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
          <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
          Active
        </label>

        <FormButton type="submit" loading={loading}>
          {zone ? 'Save changes' : 'Create zone'}
        </FormButton>
      </form>
    </Modal>
  );
}
