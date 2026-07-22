'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { WarehouseBinCreateInput } from '@/lib/inventory/warehouses';
import type { WarehouseBinItem, WarehouseBinStatus, WarehouseZoneItem } from '@/lib/types';

interface WarehouseBinFormModalProps {
  bin?: WarehouseBinItem | null;
  zones: WarehouseZoneItem[];
  onSubmit: (data: WarehouseBinCreateInput) => Promise<void>;
  onClose: () => void;
}

export function WarehouseBinFormModal({ bin, zones, onSubmit, onClose }: WarehouseBinFormModalProps) {
  const [code, setCode] = useState(bin?.code ?? '');
  const [zoneId, setZoneId] = useState(bin?.zone_id ?? '');
  const [aisle, setAisle] = useState(bin?.aisle ?? '');
  const [rack, setRack] = useState(bin?.rack ?? '');
  const [shelf, setShelf] = useState(bin?.shelf ?? '');
  const [binNumber, setBinNumber] = useState(bin?.bin_number ?? '');
  const [capacity, setCapacity] = useState(bin?.capacity != null ? String(bin.capacity) : '');
  const [statusValue, setStatusValue] = useState<WarehouseBinStatus>(bin?.status ?? 'active');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!code.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        code: code.trim(),
        zone_id: zoneId || undefined,
        aisle: aisle.trim() || undefined,
        rack: rack.trim() || undefined,
        shelf: shelf.trim() || undefined,
        bin_number: binNumber.trim() || undefined,
        capacity: capacity ? Number(capacity) : undefined,
        status: statusValue,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save bin.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={bin ? 'Edit bin location' : 'New bin location'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="max-h-[70vh] space-y-4 overflow-y-auto pr-1">
        <FormError message={error} />

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Code" htmlFor="bin-code" />
            <FormInput id="bin-code" autoFocus placeholder="A-01-01" value={code} onChange={(e) => setCode(e.target.value)} required />
          </div>
          <div>
            <FormField label="Zone" htmlFor="bin-zone" />
            <select
              id="bin-zone"
              value={zoneId}
              onChange={(e) => setZoneId(e.target.value)}
              className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
            >
              <option value="">No zone</option>
              {zones.map((zone) => (
                <option key={zone.id} value={zone.id}>{zone.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <FormField label="Aisle" htmlFor="bin-aisle" />
            <FormInput id="bin-aisle" value={aisle} onChange={(e) => setAisle(e.target.value)} />
          </div>
          <div>
            <FormField label="Rack" htmlFor="bin-rack" />
            <FormInput id="bin-rack" value={rack} onChange={(e) => setRack(e.target.value)} />
          </div>
          <div>
            <FormField label="Shelf" htmlFor="bin-shelf" />
            <FormInput id="bin-shelf" value={shelf} onChange={(e) => setShelf(e.target.value)} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Bin number" htmlFor="bin-number" />
            <FormInput id="bin-number" value={binNumber} onChange={(e) => setBinNumber(e.target.value)} />
          </div>
          <div>
            <FormField label="Capacity" htmlFor="bin-capacity" />
            <FormInput id="bin-capacity" type="number" min={0} value={capacity} onChange={(e) => setCapacity(e.target.value)} />
          </div>
        </div>

        <div>
          <FormField label="Status" htmlFor="bin-status" />
          <select
            id="bin-status"
            value={statusValue}
            onChange={(e) => setStatusValue(e.target.value as WarehouseBinStatus)}
            className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
          >
            <option value="active">Active</option>
            <option value="full">Full</option>
            <option value="blocked">Blocked</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>

        <FormButton type="submit" loading={loading}>
          {bin ? 'Save changes' : 'Create bin'}
        </FormButton>
      </form>
    </Modal>
  );
}
