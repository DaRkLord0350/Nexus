'use client';

import { ArrowLeft, Receipt, Repeat, RotateCcw } from 'lucide-react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { addCartItem, getOrCreateMyCart } from '@/lib/customer-portal/cart';
import { fetchMyOrder, fetchMyOrderInvoice, fetchMyOrderInvoiceHtml, fetchMyOrderTracking } from '@/lib/customer-portal/orders';
import type { CustomerShipmentTrackingRead, InvoiceRead, OrderDetail } from '@/lib/types';

export default function PortalOrderDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const orderId = params.id;

  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [invoice, setInvoice] = useState<InvoiceRead | null>(null);
  const [shipments, setShipments] = useState<CustomerShipmentTrackingRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [orderData, invoiceData, trackingData] = await Promise.all([
          fetchMyOrder(orderId),
          fetchMyOrderInvoice(orderId),
          fetchMyOrderTracking(orderId).catch(() => []),
        ]);
        setOrder(orderData);
        setInvoice(invoiceData);
        setShipments(trackingData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load this order.');
      } finally {
        setLoading(false);
      }
    })();
  }, [orderId]);

  const handleViewInvoice = async () => {
    try {
      const html = await fetchMyOrderInvoiceHtml(orderId);
      const blob = new Blob([html], { type: 'text/html' });
      window.open(URL.createObjectURL(blob), '_blank', 'noopener,noreferrer');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load invoice.');
    }
  };

  const handleReorder = async () => {
    if (!order) return;
    try {
      const cart = await getOrCreateMyCart(order.currency);
      for (const item of order.items) {
        await addCartItem(cart.id, cart, item.product_id, item.quantity, item.variant_id ?? undefined);
      }
      router.push('/shop/cart');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to reorder these items.');
    }
  };

  if (loading) return <SkeletonRows count={6} />;

  return (
    <div className="space-y-6">
      <Link href="/portal/dashboard/orders" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
        <ArrowLeft size={14} /> Back to orders
      </Link>

      <FormError message={error} />

      {!order ? (
        <EmptyState title="Order not found" />
      ) : (
        <>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{order.order_number}</h2>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400 capitalize">{order.status.replace(/_/g, ' ')}</p>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={handleReorder}
                  className="flex items-center gap-1.5 rounded-xl border border-slate-300 px-3.5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200"
                >
                  <Repeat size={14} /> Reorder
                </button>
                {order.status === 'delivered' ? (
                  <button
                    type="button"
                    onClick={() => router.push(`/portal/dashboard/returns/new?orderId=${order.id}`)}
                    className="flex items-center gap-1.5 rounded-xl border border-slate-300 px-3.5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200"
                  >
                    <RotateCcw size={14} /> Request return
                  </button>
                ) : null}
                {invoice ? (
                  <button type="button" onClick={handleViewInvoice} className="flex items-center gap-1.5 rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400">
                    <Receipt size={14} /> View invoice
                  </button>
                ) : null}
              </div>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
              <div>
                <p className="text-slate-400">Subtotal</p>
                <p className="font-medium text-slate-900 dark:text-white">{order.currency} {order.subtotal.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-slate-400">Tax</p>
                <p className="font-medium text-slate-900 dark:text-white">{order.currency} {order.tax_amount.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-slate-400">Shipping</p>
                <p className="font-medium text-slate-900 dark:text-white">{order.currency} {order.shipping_amount.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-slate-400">Total</p>
                <p className="font-semibold text-slate-900 dark:text-white">{order.currency} {order.total.toFixed(2)}</p>
              </div>
            </div>

            <div className="mt-4 rounded-xl border border-slate-200 p-3 text-sm dark:border-slate-800">
              <p className="mb-1 font-semibold text-slate-700 dark:text-slate-200">Shipping to</p>
              <p className="text-slate-500 dark:text-slate-400">{order.shipping_first_name} {order.shipping_last_name}</p>
              <p className="text-slate-500 dark:text-slate-400">{order.shipping_line1}, {order.shipping_city}, {order.shipping_country}</p>
            </div>
          </div>

          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Items</h3>
          <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-3">Product</th>
                  <th className="px-4 py-3">Qty</th>
                  <th className="px-4 py-3">Unit price</th>
                  <th className="px-4 py-3">Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {order.items.map((item) => (
                  <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{item.product_name}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.quantity}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{order.currency} {item.unit_price.toFixed(2)}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{order.currency} {item.total.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {shipments.length > 0 ? (
            <>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Shipment tracking</h3>
              <div className="space-y-4">
                {shipments.map((shipment) => (
                  <div key={shipment.id} className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="font-medium text-slate-900 dark:text-white">{shipment.shipment_number}</p>
                        <p className="text-sm text-slate-500 dark:text-slate-400">
                          {shipment.carrier_name ?? 'Carrier not yet assigned'} · {shipment.tracking_number ?? 'No tracking #'}
                        </p>
                      </div>
                      <span className="rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-semibold capitalize text-cyan-600 dark:text-cyan-300">
                        {shipment.status.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <div className="mt-3 space-y-2">
                      {shipment.tracking_events.length === 0 ? (
                        <p className="text-sm text-slate-500 dark:text-slate-400">No tracking updates yet.</p>
                      ) : (
                        shipment.tracking_events.map((event) => (
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
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : null}

          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Order status</h3>
          <div className="space-y-2 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
            {order.status_history.length === 0 ? (
              <p className="text-sm text-slate-500 dark:text-slate-400">No updates yet.</p>
            ) : (
              order.status_history.map((entry) => (
                <div key={entry.id} className="flex items-center justify-between text-sm">
                  <span className="capitalize text-slate-700 dark:text-slate-200">{entry.to_status.replace(/_/g, ' ')}</span>
                  <span className="text-slate-400">{new Date(entry.changed_at).toLocaleString()}</span>
                </div>
              ))
            )}
          </div>

          {order.notes.length > 0 ? (
            <>
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Notes from the seller</h3>
              <div className="space-y-2 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
                {order.notes.map((note) => (
                  <p key={note.id} className="text-sm text-slate-700 dark:text-slate-200">{note.note}</p>
                ))}
              </div>
            </>
          ) : null}
        </>
      )}
    </div>
  );
}
