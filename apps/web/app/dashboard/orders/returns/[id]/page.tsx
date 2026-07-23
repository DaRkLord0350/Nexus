'use client';

import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import {
  approveReturn,
  cancelReturn,
  completeReturn,
  fetchReturn,
  inspectReturnItem,
  receiveReturn,
  rejectReturn,
  startReturnInspection,
} from '@/lib/orders/returns';
import { createReturnShipment } from '@/lib/shipping/return-shipments';
import type { ReturnItemCondition, ReturnRequestDetail, ReturnResolution } from '@/lib/types';

const CONDITIONS: ReturnItemCondition[] = ['unopened', 'opened', 'damaged', 'defective'];
const RESOLUTIONS: ReturnResolution[] = ['refund', 'replacement', 'exchange', 'repair', 'store_credit'];

export default function ReturnDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const returnId = params.id;

  const [returnRequest, setReturnRequest] = useState<ReturnRequestDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [resolution, setResolution] = useState<ReturnResolution>('refund');

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      setReturnRequest(await fetchReturn(returnId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load return request.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (returnId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [returnId]);

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

  const handleReject = () => {
    const reason = prompt('Reason for rejecting this return?') ?? undefined;
    runAction(() => rejectReturn(returnId, reason));
  };

  const handleCancel = () => {
    if (!confirm('Cancel this return request?')) return;
    runAction(() => cancelReturn(returnId));
  };

  const handleInspectItem = (itemId: string, condition: ReturnItemCondition) => {
    runAction(() => inspectReturnItem(returnId, itemId, condition));
  };

  const handleComplete = () => {
    runAction(() => completeReturn(returnId, resolution, true));
  };

  const handleScheduleReturnShipment = () => {
    const warehouseId = prompt('Warehouse ID to receive this return at?');
    if (!warehouseId?.trim()) return;
    runAction(async () => {
      const shipment = await createReturnShipment(returnId, warehouseId.trim());
      router.push(`/dashboard/shipping/returns/${shipment.id}`);
    });
  };

  if (loading) return <SkeletonRows count={6} />;

  return (
    <div className="space-y-6">
      <Link href="/dashboard/orders/returns" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
        <ArrowLeft size={14} /> Back to returns
      </Link>

      <FormError message={error} />

      {!returnRequest ? (
        <EmptyState title="Return request not found" />
      ) : (
        <>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{returnRequest.return_number}</h2>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                  <span className="capitalize">{returnRequest.status.replace(/_/g, ' ')}</span> · Reason: <span className="capitalize">{returnRequest.reason_code.replace(/_/g, ' ')}</span>
                </p>
                <Link href={`/dashboard/orders/${returnRequest.order_id}`} className="text-sm text-cyan-600 hover:text-cyan-500 dark:text-cyan-400">
                  View order
                </Link>
              </div>

              <PermissionGuard permission="returns.manage">
                <div className="flex flex-wrap gap-2">
                  {returnRequest.status === 'requested' ? (
                    <>
                      <button type="button" disabled={actionLoading} onClick={() => runAction(() => approveReturn(returnId))} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50">Approve</button>
                      <button type="button" disabled={actionLoading} onClick={handleReject} className="rounded-xl border border-red-300 px-3.5 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50 dark:border-red-500/40 dark:text-red-400 dark:hover:bg-red-500/10">Reject</button>
                    </>
                  ) : null}
                  {returnRequest.status === 'approved' ? (
                    <>
                      <button type="button" disabled={actionLoading} onClick={handleScheduleReturnShipment} className="rounded-xl border border-cyan-400 px-3.5 py-2 text-sm font-semibold text-cyan-600 hover:bg-cyan-50 disabled:opacity-50 dark:border-cyan-500/40 dark:text-cyan-300 dark:hover:bg-cyan-500/10">Schedule return shipment</button>
                      <button type="button" disabled={actionLoading} onClick={() => runAction(() => receiveReturn(returnId))} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50">Mark received</button>
                    </>
                  ) : null}
                  {returnRequest.status === 'received' ? (
                    <button type="button" disabled={actionLoading} onClick={() => runAction(() => startReturnInspection(returnId))} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50">Start inspection</button>
                  ) : null}
                  {['requested', 'approved', 'awaiting_pickup', 'in_transit', 'received'].includes(returnRequest.status) ? (
                    <button type="button" disabled={actionLoading} onClick={handleCancel} className="rounded-xl border border-slate-300 px-3.5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:text-slate-200">Cancel</button>
                  ) : null}
                </div>
              </PermissionGuard>
            </div>
          </div>

          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Items</h3>
          <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-3">Product</th>
                  <th className="px-4 py-3">Qty</th>
                  <th className="px-4 py-3">Condition</th>
                  <th className="px-4 py-3">Restocked</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {returnRequest.items.map((item) => (
                  <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{item.product_id.slice(0, 8)}…</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.quantity}</td>
                    <td className="px-4 py-3">
                      {returnRequest.status === 'inspecting' ? (
                        <PermissionGuard permission="returns.manage">
                          <select
                            value={item.condition ?? ''}
                            onChange={(e) => handleInspectItem(item.id, e.target.value as ReturnItemCondition)}
                            className="rounded-lg border border-slate-300 bg-white px-2 py-1 text-xs text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
                          >
                            <option value="" disabled>Select…</option>
                            {CONDITIONS.map((c) => (
                              <option key={c} value={c}>{c}</option>
                            ))}
                          </select>
                        </PermissionGuard>
                      ) : (
                        <span className="capitalize text-slate-500 dark:text-slate-400">{item.condition ?? '—'}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{item.restocked ? `Yes (${item.restocked_quantity})` : 'No'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {returnRequest.status === 'inspecting' ? (
            <PermissionGuard permission="returns.manage">
              <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-200">Resolution:</span>
                <select value={resolution} onChange={(e) => setResolution(e.target.value as ReturnResolution)} className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
                  {RESOLUTIONS.map((r) => (
                    <option key={r} value={r}>{r.replace(/_/g, ' ')}</option>
                  ))}
                </select>
                <button type="button" disabled={actionLoading} onClick={handleComplete} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50">
                  Complete return &amp; restock
                </button>
              </div>
            </PermissionGuard>
          ) : null}
        </>
      )}
    </div>
  );
}
