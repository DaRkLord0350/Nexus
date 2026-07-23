'use client';

import { MapPin, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError, FormInput } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { addMyAddress, deleteMyAddress, fetchMyAddresses } from '@/lib/customer-portal/addresses';
import type { AddressItem } from '@/lib/types';

export default function PortalAddressesPage() {
  const [items, setItems] = useState<AddressItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [line1, setLine1] = useState('');
  const [city, setCity] = useState('');
  const [country, setCountry] = useState('US');

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchMyAddresses();
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load your addresses.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleAdd = async () => {
    if (!firstName.trim() || !lastName.trim() || !line1.trim() || !city.trim()) return;
    try {
      await addMyAddress({ first_name: firstName, last_name: lastName, line1, city, country });
      setFirstName('');
      setLastName('');
      setLine1('');
      setCity('');
      setShowForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to add address.');
    }
  };

  const handleDelete = async (addressId: string) => {
    if (!confirm('Delete this address?')) return;
    try {
      await deleteMyAddress(addressId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete address.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">My addresses</h2>
        <button type="button" onClick={() => setShowForm((v) => !v)} className="text-sm font-semibold text-cyan-600 hover:text-cyan-500 dark:text-cyan-400">
          {showForm ? 'Cancel' : 'Add address'}
        </button>
      </div>

      <FormError message={error} />

      {showForm ? (
        <div className="grid grid-cols-2 gap-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60 sm:grid-cols-5">
          <FormInput placeholder="First name" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
          <FormInput placeholder="Last name" value={lastName} onChange={(e) => setLastName(e.target.value)} />
          <FormInput placeholder="Address line 1" value={line1} onChange={(e) => setLine1(e.target.value)} />
          <FormInput placeholder="City" value={city} onChange={(e) => setCity(e.target.value)} />
          <div className="flex gap-2">
            <FormInput placeholder="US" maxLength={2} value={country} onChange={(e) => setCountry(e.target.value.toUpperCase())} />
            <button type="button" onClick={handleAdd} className="rounded-xl bg-cyan-500 px-3 text-sm font-semibold text-slate-950 hover:bg-cyan-400">Save</button>
          </div>
        </div>
      ) : null}

      {loading ? (
        <SkeletonRows count={3} />
      ) : items.length === 0 ? (
        <EmptyState icon={MapPin} title="No addresses on file" description="Add an address to speed up checkout." />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {items.map((address) => (
            <div key={address.id} className="flex items-start justify-between rounded-2xl border border-slate-200 bg-white p-4 text-sm dark:border-slate-800 dark:bg-slate-900/60">
              <div>
                <p className="font-medium text-slate-900 dark:text-white">
                  {address.first_name} {address.last_name} {address.is_default ? <span className="ml-1 text-xs text-cyan-600 dark:text-cyan-400">(default)</span> : null}
                </p>
                <p className="text-slate-500 dark:text-slate-400">{address.line1}, {address.city}, {address.country}</p>
              </div>
              <button type="button" onClick={() => handleDelete(address.id)} className="rounded-lg p-1.5 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10">
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
