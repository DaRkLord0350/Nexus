'use client';

import { CalendarClock } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { PermissionGuard } from '@/components/permission-guard';
import { PickupFormModal } from '@/components/shipping/pickup-form-modal';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { fetchPickups, schedulePickup, type PickupCreateInput } from '@/lib/shipping/pickups';
import type { PickupRead, PickupStatus } from '@/lib/types';

const STATUS_STYLES: Record<PickupStatus, string> = {
  scheduled: 'text-amber-600 dark:text-amber-400',
  confirmed: 'text-cyan-600 dark:text-cyan-400',
  completed: 'text-emerald-600 dark:text-emerald-400',
  cancelled: 'text-slate-500 dark:text-slate-400',
  missed: 'text-red-600 dark:text-red-400',
};

export default function PickupsPage() {
  const [items, setItems] = useState<PickupRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchPickups();
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load pickups.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSave = async (data: PickupCreateInput) => {
    await schedulePickup(data);
    await load();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Pickups</h2>
        <PermissionGuard permission="shipping.pickups.manage">
          <button type="button" onClick={() => setShowForm(true)} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400">
            Schedule pickup
          </button>
        </PermissionGuard>
      </div>

      <FormError message={error} />

      {loading ? (
        <SkeletonRows count={4} />
      ) : items.length === 0 ? (
        <EmptyState icon={CalendarClock} title="No pickups scheduled" description="Schedule a carrier pickup for one or more shipments." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr><th className="px-4 py-3">Pickup #</th><th className="px-4 py-3">Scheduled</th><th className="px-4 py-3">Time slot</th><th className="px-4 py-3">Status</th></tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {items.map((item) => (
                <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                    <Link href={`/dashboard/shipping/pickups/${item.id}`} className="hover:text-cyan-600 dark:hover:text-cyan-300">{item.pickup_number}</Link>
                  </td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{new Date(item.scheduled_date).toLocaleString()}</td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{item.time_slot ?? '—'}</td>
                  <td className="px-4 py-3"><span className={`capitalize ${STATUS_STYLES[item.status]}`}>{item.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showForm ? <PickupFormModal onSubmit={handleSave} onClose={() => setShowForm(false)} /> : null}
    </div>
  );
}
