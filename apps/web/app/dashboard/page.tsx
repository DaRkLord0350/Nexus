'use client';

import { LayoutDashboard } from 'lucide-react';
import { useEffect, useState } from 'react';
import { getDashboard } from '@/lib/api';
import { DashboardCard } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';
import { SkeletonGrid } from '@/components/ui/skeleton';
import type { DashboardResponse } from '@/lib/types';

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDashboard()
      .then(setDashboard)
      .catch((err) => setError(err instanceof Error ? err.message : 'Unable to load dashboard.'));
  }, []);

  if (error) {
    return <EmptyState icon={LayoutDashboard} title="Unable to load dashboard" description={error} />;
  }

  if (!dashboard) {
    return <SkeletonGrid />;
  }

  return (
    <div className="space-y-8">
      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        {dashboard.metrics.map((metric) => (
          <DashboardCard key={metric.id} title={metric.title} value={metric.value} subtitle={metric.subtitle} />
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <section className="space-y-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-lg shadow-slate-200/50 dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-black/10">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">Recent activity</p>
              <h2 className="text-2xl font-semibold text-slate-900 dark:text-white">Last signed in sessions</h2>
            </div>
          </div>

          <div className="space-y-4">
            {dashboard.recent_activity.length === 0 ? (
              <p className="rounded-3xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
                No recent activity yet.
              </p>
            ) : (
              dashboard.recent_activity.map((item) => (
                <article key={item.id} className="rounded-3xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/80">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="font-semibold text-slate-900 dark:text-white">{item.user_name}</p>
                      <p className="text-sm text-slate-500 dark:text-slate-400">{item.device_name ?? 'Unknown device'}</p>
                    </div>
                    <span className="rounded-full bg-slate-200 px-3 py-1 text-xs uppercase tracking-[0.24em] text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                      {item.status}
                    </span>
                  </div>
                  <div className="mt-3 text-sm text-slate-500 dark:text-slate-400">
                    <p>IP: {item.ip_address ?? 'Unknown'}</p>
                    <p>Last active: {new Date(item.last_active_at).toLocaleString()}</p>
                  </div>
                </article>
              ))
            )}
          </div>
        </section>

        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-lg shadow-slate-200/50 dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-black/10">
          <div className="space-y-3">
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">Organization summary</p>
              <h2 className="text-2xl font-semibold text-slate-900 dark:text-white">{dashboard.organization?.name ?? 'Organization'}</h2>
            </div>
            <div className="grid gap-3 text-sm text-slate-700 dark:text-slate-300">
              <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/80">
                <p className="text-slate-500 dark:text-slate-400">Slug</p>
                <p className="font-semibold text-slate-900 dark:text-white">{dashboard.organization?.slug ?? 'n/a'}</p>
              </div>
              <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/80">
                <p className="text-slate-500 dark:text-slate-400">Status</p>
                <p className="font-semibold text-slate-900 dark:text-white">{dashboard.organization?.status ?? 'n/a'}</p>
              </div>
              <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/80">
                <p className="text-slate-500 dark:text-slate-400">Generated</p>
                <p className="font-semibold text-slate-900 dark:text-white">{new Date(dashboard.summary.generated_at).toLocaleString()}</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
