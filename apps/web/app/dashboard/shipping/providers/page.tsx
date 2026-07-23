'use client';

import { Truck, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { ProviderFormModal } from '@/components/shipping/provider-form-modal';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { createShippingProvider, deleteShippingProvider, fetchShippingProviders, type ShippingProviderCreateInput } from '@/lib/shipping/providers';
import type { ShippingProviderRead } from '@/lib/types';

export default function ShippingProvidersPage() {
  const [items, setItems] = useState<ShippingProviderRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchShippingProviders();
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load shipping providers.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSave = async (data: ShippingProviderCreateInput) => {
    await createShippingProvider(data);
    await load();
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete shipping provider "${name}"?`)) return;
    try {
      await deleteShippingProvider(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete provider.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Shipping Providers</h2>
        <PermissionGuard permission="shipping.providers.manage">
          <button type="button" onClick={() => setShowForm(true)} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400">
            New provider
          </button>
        </PermissionGuard>
      </div>

      <FormError message={error} />

      {loading ? (
        <SkeletonRows count={4} />
      ) : items.length === 0 ? (
        <EmptyState icon={Truck} title="No shipping providers configured" description="Add a courier to start creating shipments." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">COD</th>
                <th className="px-4 py-3">Priority</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {items.map((item) => (
                <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                    {item.name} {item.is_default ? <span className="ml-1 text-xs text-cyan-600 dark:text-cyan-400">(default)</span> : null}
                  </td>
                  <td className="px-4 py-3 capitalize text-slate-600 dark:text-slate-300">{item.provider_type}</td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{item.supports_cod ? 'Yes' : 'No'}</td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{item.priority}</td>
                  <td className="px-4 py-3">
                    <span className={item.is_active ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}>
                      {item.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <PermissionGuard permission="shipping.providers.manage">
                      <button type="button" onClick={() => handleDelete(item.id, item.name)} className="rounded-lg p-1.5 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10">
                        <Trash2 size={16} />
                      </button>
                    </PermissionGuard>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showForm ? <ProviderFormModal onSubmit={handleSave} onClose={() => setShowForm(false)} /> : null}
    </div>
  );
}
