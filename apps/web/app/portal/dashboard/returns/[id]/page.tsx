'use client';

import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { fetchMyReturn } from '@/lib/customer-portal/returns';
import type { ReturnRequestDetail } from '@/lib/types';

export default function PortalReturnDetailPage() {
  const params = useParams<{ id: string }>();
  const returnId = params.id;

  const [returnRequest, setReturnRequest] = useState<ReturnRequestDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setReturnRequest(await fetchMyReturn(returnId));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load this return.');
      } finally {
        setLoading(false);
      }
    })();
  }, [returnId]);

  if (loading) return <SkeletonRows count={4} />;

  return (
    <div className="space-y-6">
      <Link href="/portal/dashboard/returns" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
        <ArrowLeft size={14} /> Back to returns
      </Link>

      <FormError message={error} />

      {!returnRequest ? (
        <EmptyState title="Return not found" />
      ) : (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{returnRequest.return_number}</h2>
          <p className="mt-1 text-sm capitalize text-slate-500 dark:text-slate-400">
            {returnRequest.status.replace(/_/g, ' ')} · Reason: {returnRequest.reason_code.replace(/_/g, ' ')}
          </p>
          {returnRequest.reason_notes ? <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{returnRequest.reason_notes}</p> : null}
          {returnRequest.rejected_reason ? (
            <p className="mt-2 text-sm text-red-600 dark:text-red-400">Rejected: {returnRequest.rejected_reason}</p>
          ) : null}

          <div className="mt-4 space-y-2">
            {returnRequest.items.map((item) => (
              <div key={item.id} className="flex items-center justify-between rounded-xl border border-slate-200 px-3 py-2 text-sm dark:border-slate-800">
                <span className="text-slate-700 dark:text-slate-200">Qty {item.quantity}</span>
                <span className="capitalize text-slate-500 dark:text-slate-400">{item.condition ?? 'Pending inspection'}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
