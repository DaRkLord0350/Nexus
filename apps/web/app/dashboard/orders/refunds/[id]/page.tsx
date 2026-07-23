'use client';

import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { approveRefund, completeRefund, failRefund, fetchRefund, rejectRefund } from '@/lib/orders/refunds';
import type { RefundDetail } from '@/lib/types';

export default function RefundDetailPage() {
  const params = useParams<{ id: string }>();
  const refundId = params.id;

  const [refund, setRefund] = useState<RefundDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      setRefund(await fetchRefund(refundId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load refund.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (refundId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refundId]);

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
    const reason = prompt('Reason for rejecting this refund?') ?? undefined;
    runAction(() => rejectRefund(refundId, reason));
  };

  const handleFail = () => {
    const reason = prompt('Reason for marking this refund as failed?') ?? undefined;
    runAction(() => failRefund(refundId, reason));
  };

  if (loading) return <SkeletonRows count={6} />;

  return (
    <div className="space-y-6">
      <Link href="/dashboard/orders/refunds" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
        <ArrowLeft size={14} /> Back to refunds
      </Link>

      <FormError message={error} />

      {!refund ? (
        <EmptyState title="Refund not found" />
      ) : (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{refund.refund_number}</h2>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                <span className="capitalize">{refund.status}</span> · <span className="capitalize">{refund.method.replace(/_/g, ' ')}</span> · {refund.currency} {refund.amount.toFixed(2)}
              </p>
              {refund.reason ? <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Reason: {refund.reason}</p> : null}
              <Link href={`/dashboard/orders/${refund.order_id}`} className="text-sm text-cyan-600 hover:text-cyan-500 dark:text-cyan-400">View order</Link>
            </div>

            <PermissionGuard permission="refunds.manage">
              <div className="flex flex-wrap gap-2">
                {refund.status === 'requested' ? (
                  <>
                    <button type="button" disabled={actionLoading} onClick={() => runAction(() => approveRefund(refundId))} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50">Approve</button>
                    <button type="button" disabled={actionLoading} onClick={handleReject} className="rounded-xl border border-red-300 px-3.5 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50 dark:border-red-500/40 dark:text-red-400 dark:hover:bg-red-500/10">Reject</button>
                  </>
                ) : null}
                {refund.status === 'approved' || refund.status === 'processing' ? (
                  <>
                    <button type="button" disabled={actionLoading} onClick={() => runAction(() => completeRefund(refundId))} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50">Complete</button>
                    <button type="button" disabled={actionLoading} onClick={handleFail} className="rounded-xl border border-red-300 px-3.5 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50 dark:border-red-500/40 dark:text-red-400 dark:hover:bg-red-500/10">Mark failed</button>
                  </>
                ) : null}
              </div>
            </PermissionGuard>
          </div>

          {refund.processed_at ? (
            <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">Processed at {new Date(refund.processed_at).toLocaleString()}</p>
          ) : null}
        </div>
      )}
    </div>
  );
}
