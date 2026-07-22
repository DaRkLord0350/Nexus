'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { WarehouseCreateInput } from '@/lib/inventory/warehouses';
import type { WarehouseItem, WarehouseType } from '@/lib/types';

interface WarehouseFormModalProps {
  warehouse?: WarehouseItem | null;
  onSubmit: (data: WarehouseCreateInput) => Promise<void>;
  onClose: () => void;
}

export function WarehouseFormModal({ warehouse, onSubmit, onClose }: WarehouseFormModalProps) {
  const [name, setName] = useState(warehouse?.name ?? '');
  const [code, setCode] = useState(warehouse?.code ?? '');
  const [warehouseType, setWarehouseType] = useState<WarehouseType>(warehouse?.warehouse_type ?? 'main');
  const [email, setEmail] = useState(warehouse?.email ?? '');
  const [phone, setPhone] = useState(warehouse?.phone ?? '');
  const [country, setCountry] = useState(warehouse?.country ?? '');
  const [state, setState] = useState(warehouse?.state ?? '');
  const [city, setCity] = useState(warehouse?.city ?? '');
  const [zipcode, setZipcode] = useState(warehouse?.zipcode ?? '');
  const [address, setAddress] = useState(warehouse?.address ?? '');
  const [isDefault, setIsDefault] = useState(warehouse?.is_default ?? false);
  const [isActive, setIsActive] = useState(warehouse?.is_active ?? true);
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
        warehouse_type: warehouseType,
        email: email.trim() || undefined,
        phone: phone.trim() || undefined,
        country: country.trim() || undefined,
        state: state.trim() || undefined,
        city: city.trim() || undefined,
        zipcode: zipcode.trim() || undefined,
        address: address.trim() || undefined,
        is_default: isDefault,
        is_active: isActive,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save warehouse.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={warehouse ? 'Edit warehouse' : 'New warehouse'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="max-h-[70vh] space-y-4 overflow-y-auto pr-1">
        <FormError message={error} />

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Name" htmlFor="warehouse-name" />
            <FormInput id="warehouse-name" autoFocus value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div>
            <FormField label="Code" htmlFor="warehouse-code" />
            <FormInput id="warehouse-code" value={code} onChange={(e) => setCode(e.target.value)} required />
          </div>
        </div>

        <div>
          <FormField label="Type" htmlFor="warehouse-type" />
          <select
            id="warehouse-type"
            value={warehouseType}
            onChange={(e) => setWarehouseType(e.target.value as WarehouseType)}
            className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
          >
            <option value="main">Main</option>
            <option value="retail">Retail</option>
            <option value="returns">Returns</option>
            <option value="third_party">Third-party (3PL)</option>
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Email" htmlFor="warehouse-email" />
            <FormInput id="warehouse-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <FormField label="Phone" htmlFor="warehouse-phone" />
            <FormInput id="warehouse-phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
          </div>
        </div>

        <div>
          <FormField label="Address" htmlFor="warehouse-address" />
          <FormInput id="warehouse-address" value={address} onChange={(e) => setAddress(e.target.value)} />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="City" htmlFor="warehouse-city" />
            <FormInput id="warehouse-city" value={city} onChange={(e) => setCity(e.target.value)} />
          </div>
          <div>
            <FormField label="State" htmlFor="warehouse-state" />
            <FormInput id="warehouse-state" value={state} onChange={(e) => setState(e.target.value)} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Country" htmlFor="warehouse-country" />
            <FormInput id="warehouse-country" value={country} onChange={(e) => setCountry(e.target.value)} />
          </div>
          <div>
            <FormField label="Zip code" htmlFor="warehouse-zipcode" />
            <FormInput id="warehouse-zipcode" value={zipcode} onChange={(e) => setZipcode(e.target.value)} />
          </div>
        </div>

        <div className="flex items-center gap-6">
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input type="checkbox" checked={isDefault} onChange={(e) => setIsDefault(e.target.checked)} />
            Default warehouse
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
            Active
          </label>
        </div>

        <FormButton type="submit" loading={loading}>
          {warehouse ? 'Save changes' : 'Create warehouse'}
        </FormButton>
      </form>
    </Modal>
  );
}
