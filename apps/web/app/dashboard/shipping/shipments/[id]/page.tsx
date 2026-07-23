'use client';

import { ArrowLeft, Ban, FileText, Receipt } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError, FormInput } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import {
  addShipmentTrackingEvent,
  applyShipmentTransition,
  cancelShipment,
  failShipmentDelivery,
  fetchShipment,
  fetchShipmentLabelHtml,
  fetchShipmentPackingSlipHtml,
  fetchShipmentTracking,
  type ShipmentWorkflowAction,
} from '@/lib/shipping/shipments';
import type { ShipmentDetail, ShipmentStatus, ShipmentTrackingEventRead } from '@/lib/types';

const NEXT_ACTIONS: Partial<Record<ShipmentStatus, { label: string; action: ShipmentWorkflowAction }[]>> = {
  pending: [{ label: 'Generate label', action: 'label' }],
  label_generated: [{ label: 'Mark picked up', action: 'pickup' }],
  picked_up: [{ label: 'Mark in transit', action: 'in-transit' }],
  in_transit: [{ label: 'Out for delivery', action: 'out-for-delivery' }],
  out_for_delivery: [{ label: 'Mark delivered', action: 'deliver' }],
  failed_delivery: [{ label: 'Retry: out for delivery', action: 'out-for-delivery' }, { label: 'Return to origin', action: 'return' }],
};

const CANCELLABLE = ['pending', 'label_generated', 'picked_up'];

export default function ShipmentDetailPage() {
  const params = useParams<{ id: string }>();
  const shipmentId = params.id;

  const [shipment, setShipment] = useState<ShipmentDetail | null>(null);
  const [tracking, setTracking] = useState<ShipmentTrackingEventRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [newStatus, setNewStatus] = useState('');
  const [newDescription, setNewDescription] = useState('');

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [shipmentData, trackingData] = await Promise.all([fetchShipment(shipmentId), fetchShipmentTracking(shipmentId)]);
      setShipment(shipmentData);
      setTracking(trackingData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load shipment.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (shipmentId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shipmentId]);

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
    if (!confirm('Cancel this shipment?')) return;
    runAction(() => cancelShipment(shipmentId));
  };

  const handleFailDelivery = () => {
    const reason = prompt('Reason for failed delivery?') ?? undefined;
    runAction(() => failShipmentDelivery(shipmentId, reason));
  };

  const handleAddTracking = () => {
    if (!newStatus.trim()) return;
    runAction(async () => {
      await addShipmentTrackingEvent(shipmentId, newStatus.trim(), newDescription || undefined);
      setNewStatus('');
      setNewDescription('');
    });
  };

  const openHtmlInNewTab = async (fetcher: () => Promise<string>) => {
    try {
      const html = await fetcher();
      const blob = new Blob([html], { type: 'text/html' });
      window.open(URL.createObjectURL(blob), '_blank', 'noopener,noreferrer');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load document.');
    }
  };

  if (loading) return <SkeletonRows count={6} />;

  return (
    <div className="space-y-6">
      <Link href="/dashboard/shipping/shipments" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
        <ArrowLeft size={14} /> Back to shipments
      </Link>

      <FormError message={error} />

      {!shipment ? (
        <EmptyState title="Shipment not found" />
      ) : (
        <>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{shipment.shipment_number}</h2>
                <p className="mt-1 text-sm capitalize text-slate-500 dark:text-slate-400">
                  {shipment.status.replace(/_/g, ' ')} · {shipment.carrier_name ?? 'No carrier assigned'} · {shipment.tracking_number ?? 'No tracking #'}
                </p>
              </div>
              <PermissionGuard permission="shipping.shipments.manage">
                <div className="flex flex-wrap gap-2">
                  {(NEXT_ACTIONS[shipment.status] ?? []).map((next) => (
                    <button
                      key={next.action}
                      type="button"
                      disabled={actionLoading}
                      onClick={() => runAction(() => applyShipmentTransition(shipmentId, next.action))}
                      className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50"
                    >
                      {next.label}
                    </button>
                  ))}
                  {shipment.status === 'out_for_delivery' ? (
                    <button type="button" disabled={actionLoading} onClick={handleFailDelivery} className="rounded-xl border border-red-300 px-3.5 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50 dark:border-red-500/40 dark:text-red-400 dark:hover:bg-red-500/10">
                      Mark failed
                    </button>
                  ) : null}
                  {CANCELLABLE.includes(shipment.status) ? (
                    <button type="button" disabled={actionLoading} onClick={handleCancel} className="flex items-center gap-1.5 rounded-xl border border-red-300 px-3.5 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50 dark:border-red-500/40 dark:text-red-400 dark:hover:bg-red-500/10">
                      <Ban size={14} /> Cancel
                    </button>
                  ) : null}
                </div>
              </PermissionGuard>
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              <button type="button" onClick={() => openHtmlInNewTab(() => fetchShipmentLabelHtml(shipmentId))} className="flex items-center gap-1.5 rounded-xl border border-slate-300 px-3.5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200">
                <FileText size={14} /> View label
              </button>
              <button type="button" onClick={() => openHtmlInNewTab(() => fetchShipmentPackingSlipHtml(shipmentId))} className="flex items-center gap-1.5 rounded-xl border border-slate-300 px-3.5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200">
                <Receipt size={14} /> Packing slip
              </button>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
              <div><p className="text-slate-400">Shipping cost</p><p className="font-medium text-slate-900 dark:text-white">{shipment.shipping_cost.toFixed(2)}</p></div>
              <div><p className="text-slate-400">Weight</p><p className="font-medium text-slate-900 dark:text-white">{shipment.weight ?? '—'}</p></div>
              <div><p className="text-slate-400">COD</p><p className="font-medium text-slate-900 dark:text-white">{shipment.is_cod ? `Yes (${shipment.cod_amount ?? 0})` : 'No'}</p></div>
              <div><p className="text-slate-400">Delivery attempts</p><p className="font-medium text-slate-900 dark:text-white">{shipment.delivery_attempts}</p></div>
            </div>
          </div>

          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Items</h3>
          <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                <tr><th className="px-4 py-3">Product</th><th className="px-4 py-3">SKU</th><th className="px-4 py-3">Qty</th></tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {shipment.items.map((item) => (
                  <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{item.product_name}</td>
                    <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{item.sku}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.quantity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Tracking timeline</h3>
          <div className="space-y-2 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
            {tracking.length === 0 ? (
              <p className="text-sm text-slate-500 dark:text-slate-400">No tracking events yet.</p>
            ) : (
              tracking.map((event) => (
                <div key={event.id} className="border-b border-slate-100 pb-2 text-sm last:border-0 dark:border-slate-800">
                  <div className="flex items-center justify-between">
                    <span className="font-medium capitalize text-slate-800 dark:text-slate-100">{event.status.replace(/_/g, ' ')}</span>
                    <span className="text-xs text-slate-400">{new Date(event.occurred_at).toLocaleString()}</span>
                  </div>
                  {event.description ? <p className="text-slate-500 dark:text-slate-400">{event.description}</p> : null}
                  {event.location ? <p className="text-xs text-slate-400">{event.location}</p> : null}
                </div>
              ))
            )}
            <PermissionGuard permission="shipping.shipments.manage">
              <div className="grid grid-cols-[1fr_2fr_auto] gap-2 pt-2">
                <FormInput placeholder="Status (e.g. in_transit)" value={newStatus} onChange={(e) => setNewStatus(e.target.value)} />
                <FormInput placeholder="Description" value={newDescription} onChange={(e) => setNewDescription(e.target.value)} />
                <button type="button" onClick={handleAddTracking} className="rounded-xl bg-cyan-500 px-3 text-sm font-semibold text-slate-950 hover:bg-cyan-400">Add</button>
              </div>
            </PermissionGuard>
          </div>
        </>
      )}
    </div>
  );
}
