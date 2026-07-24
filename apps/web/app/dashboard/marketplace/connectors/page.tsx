'use client';

import { Store, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { PermissionGuard } from '@/components/permission-guard';
import { ConnectorFormModal } from '@/components/marketplace/connector-form-modal';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { createMarketplaceConnector, deleteMarketplaceConnector, fetchMarketplaceConnectors, type MarketplaceConnectorCreateInput } from '@/lib/marketplace/connectors';
import type { MarketplaceConnectorRead } from '@/lib/types';

export default function MarketplaceConnectorsPage() {
  const [items, setItems] = useState<MarketplaceConnectorRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchMarketplaceConnectors();
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load marketplace connectors.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSave = async (data: MarketplaceConnectorCreateInput) => {
    await createMarketplaceConnector(data);
    await load();
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete marketplace connector "${name}"?`)) return;
    try {
      await deleteMarketplaceConnector(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete connector.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Marketplace Connectors</h2>
        <PermissionGuard permission="marketplace.connectors.manage">
          <button type="button" onClick={() => setShowForm(true)} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400">
            New connector
          </button>
        </PermissionGuard>
      </div>

      <FormError message={error} />

      {loading ? (
        <SkeletonRows count={4} />
      ) : items.length === 0 ? (
        <EmptyState icon={Store} title="No marketplace connectors configured" description="Connect a WooCommerce, Amazon, Flipkart, Shopify, Etsy, or eBay store to start syncing." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Marketplace</th>
                <th className="px-4 py-3">Last sync</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {items.map((item) => (
                <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                    <Link href={`/dashboard/marketplace/connectors/${item.id}`} className="hover:text-cyan-600 dark:hover:text-cyan-300">{item.name}</Link>
                  </td>
                  <td className="px-4 py-3 capitalize text-slate-600 dark:text-slate-300">{item.connector_type}</td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">
                    {item.last_sync_at ? new Date(item.last_sync_at).toLocaleString() : 'Never'}
                    {item.last_sync_status ? <span className="ml-1 capitalize">({item.last_sync_status})</span> : null}
                  </td>
                  <td className="px-4 py-3">
                    <span className={item.is_active ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}>
                      {item.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <PermissionGuard permission="marketplace.connectors.manage">
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

      {showForm ? <ConnectorFormModal onSubmit={handleSave} onClose={() => setShowForm(false)} /> : null}
    </div>
  );
}
