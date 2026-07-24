'use client';

import { useEffect, useState } from 'react';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { fetchMarketplaceAnalytics } from '@/lib/marketplace/analytics';
import type { MarketplaceAnalyticsResponse } from '@/lib/types';

export default function MarketplaceAnalyticsPage() {
  const [report, setReport] = useState<MarketplaceAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setReport(await fetchMarketplaceAnalytics());
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
      <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Marketplace Analytics</h2>
      <FormError message={error} />

      {!report || report.summary.total_syncs === 0 ? (
        <EmptyState title="No sync activity yet" description="Analytics will appear once a connector runs its first sync." />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
              <p className="text-xs uppercase text-slate-400">Total syncs</p>
              <p className="mt-1 text-2xl font-semibold text-slate-900 dark:text-white">{report.summary.total_syncs}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
              <p className="text-xs uppercase text-slate-400">Sync success rate</p>
              <p className="mt-1 text-2xl font-semibold text-emerald-600 dark:text-emerald-400">{report.summary.sync_success_rate}%</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
              <p className="text-xs uppercase text-slate-400">Orders imported</p>
              <p className="mt-1 text-2xl font-semibold text-slate-900 dark:text-white">{report.summary.total_orders_imported}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
              <p className="text-xs uppercase text-slate-400">Revenue imported</p>
              <p className="mt-1 text-2xl font-semibold text-slate-900 dark:text-white">{report.summary.total_revenue_imported.toFixed(2)}</p>
            </div>
          </div>

          {report.summary.pending_webhook_retries > 0 ? (
            <div className="rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-700 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-300">
              {report.summary.pending_webhook_retries} webhook event(s) are currently failed and awaiting retry.
            </div>
          ) : null}

          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">By connector</h3>
          <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-3">Connector</th>
                  <th className="px-4 py-3">Syncs</th>
                  <th className="px-4 py-3">Success %</th>
                  <th className="px-4 py-3">Orders imported</th>
                  <th className="px-4 py-3">Revenue</th>
                  <th className="px-4 py-3">Products linked</th>
                  <th className="px-4 py-3">Avg duration (s)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {report.connectors.map((c) => (
                  <tr key={c.marketplace_connector_id} className="bg-white dark:bg-slate-900/40">
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{c.connector_name}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{c.total_syncs}</td>
                    <td className="px-4 py-3 text-emerald-600 dark:text-emerald-400">{c.sync_success_rate}%</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{c.orders_imported}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{c.revenue_imported.toFixed(2)}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{c.products_linked}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{c.avg_sync_duration_seconds ?? '—'}</td>
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
