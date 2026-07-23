'use client';

import { ArrowLeft, Ban, PauseCircle, PlayCircle, Receipt } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormButton, FormError, FormInput } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import {
  addOrderNote,
  applyOrderTransition,
  cancelOrder,
  createOrderPayment,
  fetchInvoiceHtml,
  fetchOrder,
  fetchOrderInvoice,
  fetchOrderPayments,
  generateOrderInvoice,
  holdOrder,
  refundOrderPayment,
  type OrderWorkflowAction,
} from '@/lib/orders/orders';
import type { InvoiceRead, OrderDetail, OrderStatus, PaymentAttemptRead } from '@/lib/types';

const NEXT_ACTIONS: Partial<Record<OrderStatus, { label: string; action: OrderWorkflowAction }[]>> = {
  draft: [{ label: 'Place order', action: 'place' }],
  pending: [{ label: 'Confirm', action: 'confirm' }],
  confirmed: [{ label: 'Start processing', action: 'process' }],
  processing: [
    { label: 'Mark packed', action: 'pack' },
    { label: 'Partially fulfilled', action: 'partially-fulfill' },
    { label: 'Backorder', action: 'backorder' },
  ],
  packed: [{ label: 'Ready to ship', action: 'ready-to-ship' }],
  ready_to_ship: [{ label: 'Ship', action: 'ship' }],
  shipped: [
    { label: 'Out for delivery', action: 'out-for-delivery' },
    { label: 'Mark delivered', action: 'deliver' },
  ],
  out_for_delivery: [{ label: 'Mark delivered', action: 'deliver' }],
  partially_fulfilled: [
    { label: 'Continue processing', action: 'process' },
    { label: 'Mark packed', action: 'pack' },
  ],
  backordered: [{ label: 'Continue processing', action: 'process' }],
  hold: [{ label: 'Resume', action: 'resume' }],
};

const CANCELLABLE_STATUSES: OrderStatus[] = ['draft', 'pending', 'confirmed', 'processing', 'packed', 'ready_to_ship', 'partially_fulfilled', 'backordered'];
const HOLDABLE_STATUSES: OrderStatus[] = ['pending', 'confirmed', 'processing', 'packed', 'ready_to_ship'];

export default function OrderDetailPage() {
  const params = useParams<{ id: string }>();
  const orderId = params.id;

  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [payments, setPayments] = useState<PaymentAttemptRead[]>([]);
  const [invoice, setInvoice] = useState<InvoiceRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [newNote, setNewNote] = useState('');
  const [paymentAmount, setPaymentAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('card');

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [orderData, paymentsData, invoiceData] = await Promise.all([
        fetchOrder(orderId),
        fetchOrderPayments(orderId),
        fetchOrderInvoice(orderId),
      ]);
      setOrder(orderData);
      setPayments(paymentsData);
      setInvoice(invoiceData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load order.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (orderId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orderId]);

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
    if (!confirm('Cancel this order? Any allocated inventory will be restocked.')) return;
    runAction(() => cancelOrder(orderId));
  };

  const handleHold = () => runAction(() => holdOrder(orderId));

  const handleAddNote = () => {
    if (!newNote.trim()) return;
    runAction(async () => {
      await addOrderNote(orderId, newNote.trim());
      setNewNote('');
    });
  };

  const handleAddPayment = () => {
    const amount = Number(paymentAmount);
    if (!amount || amount <= 0) return;
    runAction(async () => {
      await createOrderPayment(orderId, paymentMethod, amount);
      setPaymentAmount('');
    });
  };

  const handleRefund = () => {
    const amount = Number(paymentAmount);
    if (!amount || amount <= 0) return;
    runAction(async () => {
      await refundOrderPayment(orderId, amount);
      setPaymentAmount('');
    });
  };

  const handleGenerateInvoice = () => runAction(() => generateOrderInvoice(orderId));

  const handleViewInvoice = async () => {
    if (!invoice) return;
    try {
      const html = await fetchInvoiceHtml(invoice.id);
      const blob = new Blob([html], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank', 'noopener,noreferrer');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load invoice.');
    }
  };

  if (loading) return <SkeletonRows count={8} />;

  return (
    <div className="space-y-6">
      <Link href="/dashboard/orders" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
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
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                  <span className="capitalize">{order.status.replace(/_/g, ' ')}</span> · <span className="capitalize">{order.priority}</span> priority ·{' '}
                  <span className="capitalize">{order.payment_status.replace(/_/g, ' ')}</span>
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <PermissionGuard permission="orders.edit">
                  {(NEXT_ACTIONS[order.status] ?? []).map((next) => (
                    <button
                      key={next.action}
                      type="button"
                      disabled={actionLoading}
                      onClick={() => runAction(() => applyOrderTransition(orderId, next.action))}
                      className="flex items-center gap-1.5 rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50"
                    >
                      <PlayCircle size={14} /> {next.label}
                    </button>
                  ))}
                  {HOLDABLE_STATUSES.includes(order.status) ? (
                    <button type="button" disabled={actionLoading} onClick={handleHold} className="flex items-center gap-1.5 rounded-xl border border-amber-300 px-3.5 py-2 text-sm font-semibold text-amber-600 hover:bg-amber-50 disabled:opacity-50 dark:border-amber-500/40 dark:text-amber-400 dark:hover:bg-amber-500/10">
                      <PauseCircle size={14} /> Hold
                    </button>
                  ) : null}
                </PermissionGuard>
                <PermissionGuard permission="orders.cancel">
                  {CANCELLABLE_STATUSES.includes(order.status) ? (
                    <button type="button" disabled={actionLoading} onClick={handleCancel} className="flex items-center gap-1.5 rounded-xl border border-red-300 px-3.5 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50 dark:border-red-500/40 dark:text-red-400 dark:hover:bg-red-500/10">
                      <Ban size={14} /> Cancel
                    </button>
                  ) : null}
                </PermissionGuard>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-4 text-sm sm:grid-cols-5">
              <div>
                <p className="text-slate-400">Subtotal</p>
                <p className="font-medium text-slate-900 dark:text-white">{order.currency} {order.subtotal.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-slate-400">Discount</p>
                <p className="font-medium text-slate-900 dark:text-white">-{order.currency} {order.discount_amount.toFixed(2)}</p>
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

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl border border-slate-200 p-3 text-sm dark:border-slate-800">
                <p className="mb-1 font-semibold text-slate-700 dark:text-slate-200">Billing address</p>
                <p className="text-slate-500 dark:text-slate-400">{order.billing_first_name} {order.billing_last_name}</p>
                <p className="text-slate-500 dark:text-slate-400">{order.billing_line1}, {order.billing_city}, {order.billing_country}</p>
              </div>
              <div className="rounded-xl border border-slate-200 p-3 text-sm dark:border-slate-800">
                <p className="mb-1 font-semibold text-slate-700 dark:text-slate-200">Shipping address</p>
                <p className="text-slate-500 dark:text-slate-400">{order.shipping_first_name} {order.shipping_last_name}</p>
                <p className="text-slate-500 dark:text-slate-400">{order.shipping_line1}, {order.shipping_city}, {order.shipping_country}</p>
              </div>
            </div>
          </div>

          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Line items ({order.items.length})</h3>
          <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-3">Product</th>
                  <th className="px-4 py-3">SKU</th>
                  <th className="px-4 py-3">Qty</th>
                  <th className="px-4 py-3">Unit price</th>
                  <th className="px-4 py-3">Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {order.items.map((item) => (
                  <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{item.product_name}</td>
                    <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{item.sku}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.quantity}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{order.currency} {item.unit_price.toFixed(2)}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{order.currency} {item.total.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Timeline</h3>
              <div className="space-y-2 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
                {order.status_history.length === 0 ? (
                  <p className="text-sm text-slate-500 dark:text-slate-400">No status changes yet.</p>
                ) : (
                  order.status_history.map((entry) => (
                    <div key={entry.id} className="flex items-center justify-between text-sm">
                      <span className="capitalize text-slate-700 dark:text-slate-200">
                        {entry.from_status ? `${entry.from_status.replace(/_/g, ' ')} → ` : ''}{entry.to_status.replace(/_/g, ' ')}
                      </span>
                      <span className="text-slate-400">{new Date(entry.changed_at).toLocaleString()}</span>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Notes</h3>
              <div className="space-y-2 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
                {order.notes.length === 0 ? (
                  <p className="text-sm text-slate-500 dark:text-slate-400">No notes yet.</p>
                ) : (
                  order.notes.map((note) => (
                    <div key={note.id} className="border-b border-slate-100 pb-2 text-sm last:border-0 dark:border-slate-800">
                      <p className="text-slate-700 dark:text-slate-200">{note.note}</p>
                      <p className="text-xs text-slate-400">{new Date(note.created_at).toLocaleString()}</p>
                    </div>
                  ))
                )}
                <PermissionGuard permission="orders.edit">
                  <div className="flex gap-2 pt-2">
                    <FormInput placeholder="Add a note…" value={newNote} onChange={(e) => setNewNote(e.target.value)} />
                    <button type="button" onClick={handleAddNote} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400">
                      Add
                    </button>
                  </div>
                </PermissionGuard>
              </div>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Payments</h3>
              <div className="space-y-2 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Paid: {order.currency} {order.amount_paid.toFixed(2)} · Refunded: {order.currency} {order.amount_refunded.toFixed(2)}
                </p>
                {payments.length === 0 ? (
                  <p className="text-sm text-slate-500 dark:text-slate-400">No payment attempts yet.</p>
                ) : (
                  payments.map((payment) => (
                    <div key={payment.id} className="flex items-center justify-between border-b border-slate-100 py-1.5 text-sm last:border-0 dark:border-slate-800">
                      <span className="capitalize text-slate-700 dark:text-slate-200">{payment.method} · {payment.status}</span>
                      <span className="text-slate-500 dark:text-slate-400">{payment.currency} {payment.amount.toFixed(2)}</span>
                    </div>
                  ))
                )}
                <PermissionGuard permission="orders.edit">
                  <div className="grid grid-cols-[1fr_1fr_auto_auto] gap-2 pt-2">
                    <select value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)} className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
                      <option value="card">Card</option>
                      <option value="cod">COD</option>
                      <option value="wallet">Wallet</option>
                    </select>
                    <FormInput type="number" min={0} step="0.01" placeholder="Amount" value={paymentAmount} onChange={(e) => setPaymentAmount(e.target.value)} />
                    <button type="button" onClick={handleAddPayment} className="rounded-xl bg-cyan-500 px-3 text-sm font-semibold text-slate-950 hover:bg-cyan-400">Charge</button>
                    <button type="button" onClick={handleRefund} className="rounded-xl border border-slate-300 px-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200">Refund</button>
                  </div>
                </PermissionGuard>
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Invoice</h3>
              <div className="space-y-2 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
                {invoice ? (
                  <>
                    <p className="text-sm text-slate-700 dark:text-slate-200">{invoice.invoice_number} · <span className="capitalize">{invoice.status}</span></p>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Due: {invoice.currency} {invoice.amount_due.toFixed(2)}</p>
                    <button
                      type="button"
                      onClick={handleViewInvoice}
                      className="inline-flex items-center gap-1.5 text-sm font-semibold text-cyan-600 hover:text-cyan-500 dark:text-cyan-400"
                    >
                      <Receipt size={14} /> View invoice
                    </button>
                  </>
                ) : (
                  <>
                    <p className="text-sm text-slate-500 dark:text-slate-400">No invoice generated yet.</p>
                    <PermissionGuard permission="orders.edit">
                      <FormButton type="button" onClick={handleGenerateInvoice}>Generate invoice</FormButton>
                    </PermissionGuard>
                  </>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
