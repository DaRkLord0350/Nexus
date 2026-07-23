'use client';

import { useEffect, useState } from 'react';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { fetchCourierPerformance } from '@/lib/shipping/analytics';
import type { CourierPerformanceResponse } from '@/lib/types';

export default function ShippingAnalyticsPage() {
  const [report, setReport] = useState<CourierPerformanceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setReport(await fetchCourierPerformance());
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load analytics.');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <SkeletonRows count={6} />;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Shipping Analytics</h2>
      <FormError message={error} />

      {!report || report.summary.total_shipments === 0 ? (
        <EmptyState title="No shipment data yet" description="Analytics will appear once shipments are created and tracked." />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
              <p className="text-xs uppercase text-slate-400">Total shipments</p>
              <p className="mt-1 text-2xl font-semibold text-slate-900 dark:text-white">{report.summary.total_shipments}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
              <p className="text-xs uppercase text-slate-400">Delivered</p>
              <p className="mt-1 text-2xl font-semibold text-emerald-600 dark:text-emerald-400">{report.summary.delivered_rate}%</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
              <p className="text-xs uppercase text-slate-400">Failed delivery (NDR)</p>
              <p className="mt-1 text-2xl font-semibold text-red-600 dark:text-red-400">{report.summary.failed_delivery_rate}%</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
              <p className="text-xs uppercase text-slate-400">Total shipping cost</p>
              <p className="mt-1 text-2xl font-semibold text-slate-900 dark:text-white">{report.summary.total_shipping_cost.toFixed(2)}</p>
            </div>
          </div>

          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Courier performance</h3>
          <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-3">Provider</th>
                  <th className="px-4 py-3">Shipments</th>
                  <th className="px-4 py-3">Delivered %</th>
                  <th className="px-4 py-3">Failed % (NDR)</th>
                  <th className="px-4 py-3">COD %</th>
                  <th className="px-4 py-3">Avg transit (days)</th>
                  <th className="px-4 py-3">SLA met %</th>
                  <th className="px-4 py-3">Total cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {report.providers.map((p) => (
                  <tr key={p.shipping_provider_id} className="bg-white dark:bg-slate-900/40">
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{p.provider_name}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{p.total_shipments}</td>
                    <td className="px-4 py-3 text-emerald-600 dark:text-emerald-400">{p.delivered_rate}%</td>
                    <td className="px-4 py-3 text-red-600 dark:text-red-400">{p.failed_delivery_rate}%</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{p.cod_rate}%</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{p.avg_transit_days ?? '—'}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{p.sla_met_rate ?? '—'}{p.sla_met_rate !== null ? '%' : ''}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{p.total_shipping_cost.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
