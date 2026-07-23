'use client';

import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import {
  cancelReturnShipment,
  fetchReturnShipment,
  generateReturnLabel,
  markReturnShipmentInTransit,
  markReturnShipmentReceived,
  scheduleReversePickup,
} from '@/lib/shipping/return-shipments';
import type { ReturnShipmentRead } from '@/lib/types';

export default function ReturnShipmentDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;

  const [returnShipment, setReturnShipment] = useState<ReturnShipmentRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      setReturnShipment(await fetchReturnShipment(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load return shipment.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

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

  const handleSchedulePickup = () => {
    const input = prompt('Schedule reverse pickup for (YYYY-MM-DD HH:MM)?');
    if (!input) return;
    const date = new Date(input);
    if (Number.isNaN(date.getTime())) {
      setError('Invalid date format.');
      return;
    }
    runAction(() => scheduleReversePickup(id, date.toISOString()));
  };

  const handleCancel = () => {
    const reason = prompt('Reason for cancelling?') ?? undefined;
    runAction(() => cancelReturnShipment(id, reason));
  };

  if (loading) return <SkeletonRows count={4} />;

  return (
    <div className="space-y-6">
      <Link href="/dashboard/shipping/returns" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
        <ArrowLeft size={14} /> Back to return shipments
      </Link>

      <FormError message={error} />

      {!returnShipment ? (
        <EmptyState title="Return shipment not found" />
      ) : (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{returnShipment.return_shipment_number}</h2>
              <p className="mt-1 text-sm capitalize text-slate-500 dark:text-slate-400">
                {returnShipment.status.replace(/_/g, ' ')} · {returnShipment.tracking_number ?? 'No tracking #'}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {returnShipment.status === 'pending' ? (
                <button type="button" disabled={actionLoading} onClick={() => runAction(() => generateReturnLabel(id))} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50">Generate label</button>
              ) : null}
              {returnShipment.status === 'label_generated' ? (
                <button type="button" disabled={actionLoading} onClick={handleSchedulePickup} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50">Schedule reverse pickup</button>
              ) : null}
              {returnShipment.status === 'reverse_pickup_scheduled' ? (
                <button type="button" disabled={actionLoading} onClick={() => runAction(() => markReturnShipmentInTransit(id))} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50">Mark in transit</button>
              ) : null}
              {returnShipment.status === 'in_transit' ? (
                <button type="button" disabled={actionLoading} onClick={() => runAction(() => markReturnShipmentReceived(id))} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50">Mark received</button>
              ) : null}
              {['pending', 'label_generated', 'reverse_pickup_scheduled', 'in_transit'].includes(returnShipment.status) ? (
                <button type="button" disabled={actionLoading} onClick={handleCancel} className="rounded-xl border border-red-300 px-3.5 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50 dark:border-red-500/40 dark:text-red-400 dark:hover:bg-red-500/10">Cancel</button>
              ) : null}
            </div>
          </div>

          <div className="mt-4 rounded-xl border border-slate-200 p-3 text-sm dark:border-slate-800">
            <p className="mb-1 font-semibold text-slate-700 dark:text-slate-200">Pickup from</p>
            <p className="text-slate-500 dark:text-slate-400">{returnShipment.pickup_contact_name} {returnShipment.pickup_contact_phone}</p>
            <p className="text-slate-500 dark:text-slate-400">{returnShipment.pickup_line1}, {returnShipment.pickup_city}, {returnShipment.pickup_country}</p>
          </div>
        </div>
      )}
    </div>
  );
}
