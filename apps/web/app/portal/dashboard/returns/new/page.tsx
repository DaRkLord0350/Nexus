'use client';

import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { EmptyState } from '@/components/ui/empty-state';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { fetchMyOrder } from '@/lib/customer-portal/orders';
import { createMyReturn } from '@/lib/customer-portal/returns';
import type { OrderDetail } from '@/lib/types';

const REASON_CODES = ['damaged', 'wrong_item', 'not_as_described', 'no_longer_needed', 'defective', 'other'];

export default function PortalNewReturnPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const orderId = searchParams.get('orderId') ?? '';

  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [orderItemId, setOrderItemId] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [reasonCode, setReasonCode] = useState('damaged');
  const [reasonNotes, setReasonNotes] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!orderId) {
      setLoading(false);
      return;
    }
    (async () => {
      try {
        const data = await fetchMyOrder(orderId);
        setOrder(data);
        if (data.items.length > 0) setOrderItemId(data.items[0].id);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load this order.');
      } finally {
        setLoading(false);
      }
    })();
  }, [orderId]);

  const handleSubmit = async () => {
    if (!orderItemId) return;
    setSaving(true);
    setError(null);
    try {
      const created = await createMyReturn({
        order_id: orderId,
        reason_code: reasonCode,
        reason_notes: reasonNotes || undefined,
        items: [{ order_item_id: orderItemId, quantity: Number(quantity) || 1 }],
      });
      router.push(`/portal/dashboard/returns/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to submit return request.');
    } finally {
      setSaving(false);
    }
  };

  if (!orderId) return <EmptyState title="No order selected" description="Start a return from an order's detail page." />;
  if (loading) return <SkeletonRows count={4} />;

  return (
    <div className="space-y-6">
      <Link href={`/portal/dashboard/orders/${orderId}`} className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
        <ArrowLeft size={14} /> Back to order
      </Link>

      <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Request a return</h2>
      <FormError message={error} />

      {!order ? (
        <EmptyState title="Order not found" />
      ) : (
        <div className="max-w-lg space-y-4 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
          <div>
            <FormField label="Item" htmlFor="order_item" />
            <select
              id="order_item"
              value={orderItemId}
              onChange={(e) => setOrderItemId(e.target.value)}
              className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
            >
              {order.items.map((item) => (
                <option key={item.id} value={item.id}>{item.product_name} (qty {item.quantity})</option>
              ))}
            </select>
          </div>
          <div>
            <FormField label="Quantity to return" htmlFor="quantity" />
            <FormInput id="quantity" type="number" min={1} value={quantity} onChange={(e) => setQuantity(e.target.value)} />
          </div>
          <div>
            <FormField label="Reason" htmlFor="reason_code" />
            <select
              id="reason_code"
              value={reasonCode}
              onChange={(e) => setReasonCode(e.target.value)}
              className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
            >
              {REASON_CODES.map((code) => (
                <option key={code} value={code}>{code.replace(/_/g, ' ')}</option>
              ))}
            </select>
          </div>
          <div>
            <FormField label="Additional details (optional)" htmlFor="reason_notes" />
            <FormInput id="reason_notes" value={reasonNotes} onChange={(e) => setReasonNotes(e.target.value)} />
          </div>
          <FormButton type="button" loading={saving} onClick={handleSubmit}>
            Submit return request
          </FormButton>
        </div>
      )}
    </div>
  );
}
