'use client';

import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { cancelPickup, completePickup, confirmPickup, fetchPickup, markPickupMissed } from '@/lib/shipping/pickups';
import type { PickupRead } from '@/lib/types';

export default function PickupDetailPage() {
  const params = useParams<{ id: string }>();
  const pickupId = params.id;

  const [pickup, setPickup] = useState<PickupRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      setPickup(await fetchPickup(pickupId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load pickup.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (pickupId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pickupId]);

  const runAction = async (fn: () => Promise<unknown>) => {
    setActionLoading(true);
    setError(null);
    try {
      await fn();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = () => {
    const reason = prompt('Reason for cancelling this pickup?') ?? undefined;
    runAction(() => cancelPickup(pickupId, reason));
  };

  if (loading) return <SkeletonRows count={4} />;

  return (
    <div className="space-y-6">
      <Link href="/dashboard/shipping/pickups" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
        <ArrowLeft size={14} /> Back to pickups
      </Link>

      <FormError message={error} />

      {!pickup ? (
        <EmptyState title="Pickup not found" />
      ) : (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{pickup.pickup_number}</h2>
              <p className="mt-1 text-sm capitalize text-slate-500 dark:text-slate-400">
                {pickup.status} · {new Date(pickup.scheduled_date).toLocaleString()} {pickup.time_slot ? `(${pickup.time_slot})` : ''}
              </p>
            </div>
            <PermissionGuard permission="shipping.pickups.manage">
              <div className="flex flex-wrap gap-2">
                {pickup.status === 'scheduled' ? (
                  <button type="button" disabled={actionLoading} onClick={() => runAction(() => confirmPickup(pickupId))} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50">Confirm</button>
                ) : null}
                {pickup.status === 'confirmed' ? (
                  <button type="button" disabled={actionLoading} onClick={() => runAction(() => completePickup(pickupId))} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50">Complete</button>
                ) : null}
                {(pickup.status === 'scheduled' || pickup.status === 'confirmed') ? (
                  <button type="button" disabled={actionLoading} onClick={() => runAction(() => markPickupMissed(pickupId))} className="rounded-xl border border-amber-300 px-3.5 py-2 text-sm font-semibold text-amber-600 hover:bg-amber-50 disabled:opacity-50 dark:border-amber-500/40 dark:text-amber-400 dark:hover:bg-amber-500/10">Mark missed</button>
                ) : null}
                {(pickup.status === 'scheduled' || pickup.status === 'confirmed' || pickup.status === 'missed') ? (
                  <button type="button" disabled={actionLoading} onClick={handleCancel} className="rounded-xl border border-red-300 px-3.5 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50 dark:border-red-500/40 dark:text-red-400 dark:hover:bg-red-500/10">Cancel</button>
                ) : null}
              </div>
            </PermissionGuard>
          </div>

          {pickup.contact_name || pickup.contact_phone ? (
            <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">Contact: {pickup.contact_name} {pickup.contact_phone}</p>
          ) : null}
          {pickup.notes ? <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{pickup.notes}</p> : null}
          {pickup.cancelled_reason ? <p className="mt-2 text-sm text-red-600 dark:text-red-400">Cancelled: {pickup.cancelled_reason}</p> : null}
        </div>
      )}
    </div>
  );
}
