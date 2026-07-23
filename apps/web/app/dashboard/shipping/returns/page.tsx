'use client';

import { RotateCcw } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { fetchReturnShipments } from '@/lib/shipping/return-shipments';
import type { ReturnShipmentRead } from '@/lib/types';

export default function ReturnShipmentsPage() {
  const [items, setItems] = useState<ReturnShipmentRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await fetchReturnShipments();
        setItems(data.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load return shipments.');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Return Shipments</h2>
      <FormError message={error} />

      {loading ? (
        <SkeletonRows count={4} />
      ) : items.length === 0 ? (
        <EmptyState icon={RotateCcw} title="No reverse-logistics shipments" description="Create one from an approved return request." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr><th className="px-4 py-3">Return shipment #</th><th className="px-4 py-3">Tracking #</th><th className="px-4 py-3">Status</th></tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {items.map((item) => (
                <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                    <Link href={`/dashboard/shipping/returns/${item.id}`} className="hover:text-cyan-600 dark:hover:text-cyan-300">{item.return_shipment_number}</Link>
                  </td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{item.tracking_number ?? '—'}</td>
                  <td className="px-4 py-3 capitalize text-slate-600 dark:text-slate-300">{item.status.replace(/_/g, ' ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
