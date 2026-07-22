'use client';

import { ArrowLeft, Plus, Send, Trash2, XCircle } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError, FormInput } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import {
  addPurchaseOrderItem,
  cancelPurchaseOrder,
  fetchPurchaseOrder,
  removePurchaseOrderItem,
  sendPurchaseOrder,
} from '@/lib/inventory/purchase-orders';
import type { PurchaseOrderDetail } from '@/lib/types';

export default function PurchaseOrderDetailPage() {
  const params = useParams<{ id: string }>();
  const poId = params.id;

  const [po, setPo] = useState<PurchaseOrderDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newProductId, setNewProductId] = useState('');
  const [newQuantity, setNewQuantity] = useState('1');
  const [newUnitCost, setNewUnitCost] = useState('0');
  const [actionLoading, setActionLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchPurchaseOrder(poId);
      setPo(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load purchase order.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (poId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [poId]);

  const handleAddItem = async () => {
    if (!newProductId.trim()) return;
    try {
      await addPurchaseOrderItem(poId, { product_id: newProductId.trim(), quantity_ordered: Number(newQuantity), unit_cost: Number(newUnitCost) });
      setNewProductId('');
      setNewQuantity('1');
      setNewUnitCost('0');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to add item.');
    }
  };

  const handleRemoveItem = async (itemId: string) => {
    try {
      await removePurchaseOrderItem(poId, itemId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to remove item.');
    }
  };

  const handleSend = async () => {
    setActionLoading(true);
    try {
      await sendPurchaseOrder(poId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to send purchase order.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm('Cancel this purchase order?')) return;
    setActionLoading(true);
    try {
      await cancelPurchaseOrder(poId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to cancel purchase order.');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <SkeletonRows count={6} />;

  return (
    <div className="space-y-6">
      <Link href="/dashboard/inventory/purchase-orders" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
        <ArrowLeft size={14} /> Back to purchase orders
      </Link>

      <FormError message={error} />

      {!po ? (
        <EmptyState title="Purchase order not found" />
      ) : (
        <>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{po.po_number}</h2>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                  {po.supplier_name} · <span className="capitalize">{po.status.replace('_', ' ')}</span>
                </p>
              </div>
              <div className="flex gap-2">
                {po.status === 'draft' ? (
                  <PermissionGuard permission="inventory.purchase_orders.edit">
                    <button
                      type="button"
                      onClick={handleSend}
                      disabled={actionLoading}
                      className="flex items-center gap-1.5 rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50"
                    >
                      <Send size={14} /> Send
                    </button>
                  </PermissionGuard>
                ) : null}
                {po.status === 'draft' || po.status === 'sent' ? (
                  <PermissionGuard permission="inventory.purchase_orders.edit">
                    <button
                      type="button"
                      onClick={handleCancel}
                      disabled={actionLoading}
                      className="flex items-center gap-1.5 rounded-xl border border-red-300 px-3.5 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50 dark:border-red-500/40 dark:text-red-400 dark:hover:bg-red-500/10"
                    >
                      <XCircle size={14} /> Cancel
                    </button>
                  </PermissionGuard>
                ) : null}
              </div>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
              <div>
                <p className="text-slate-400">Subtotal</p>
                <p className="font-medium text-slate-900 dark:text-white">{po.currency} {po.subtotal.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-slate-400">Tax</p>
                <p className="font-medium text-slate-900 dark:text-white">{po.currency} {po.tax_amount.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-slate-400">Shipping</p>
                <p className="font-medium text-slate-900 dark:text-white">{po.currency} {po.shipping_amount.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-slate-400">Total</p>
                <p className="font-semibold text-slate-900 dark:text-white">{po.currency} {po.total.toFixed(2)}</p>
              </div>
            </div>
          </div>

          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Line items ({po.items.length})</h3>

          {po.status === 'draft' ? (
            <PermissionGuard permission="inventory.purchase_orders.edit">
              <div className="grid grid-cols-[2fr_1fr_1fr_auto] gap-2 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
                <FormInput placeholder="Product ID" value={newProductId} onChange={(e) => setNewProductId(e.target.value)} />
                <FormInput type="number" min={1} placeholder="Qty" value={newQuantity} onChange={(e) => setNewQuantity(e.target.value)} />
                <FormInput type="number" min={0} step="0.01" placeholder="Unit cost" value={newUnitCost} onChange={(e) => setNewUnitCost(e.target.value)} />
                <button type="button" onClick={handleAddItem} className="flex items-center justify-center gap-1.5 rounded-xl bg-cyan-500 px-3 text-sm font-semibold text-slate-950 hover:bg-cyan-400">
                  <Plus size={14} /> Add
                </button>
              </div>
            </PermissionGuard>
          ) : null}

          {po.items.length === 0 ? (
            <EmptyState title="No line items yet" />
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                  <tr>
                    <th className="px-4 py-3">Product</th>
                    <th className="px-4 py-3">Ordered</th>
                    <th className="px-4 py-3">Received</th>
                    <th className="px-4 py-3">Unit cost</th>
                    <th className="px-4 py-3">Line total</th>
                    {po.status === 'draft' ? <th className="px-4 py-3 text-right">Actions</th> : null}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {po.items.map((item) => (
                    <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                      <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{item.product_id.slice(0, 8)}…</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.quantity_ordered}</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.quantity_received}</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{po.currency} {item.unit_cost.toFixed(2)}</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{po.currency} {(item.unit_cost * item.quantity_ordered).toFixed(2)}</td>
                      {po.status === 'draft' ? (
                        <td className="px-4 py-3 text-right">
                          <PermissionGuard permission="inventory.purchase_orders.edit">
                            <button type="button" onClick={() => handleRemoveItem(item.id)} className="rounded-lg p-1.5 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10">
                              <Trash2 size={16} />
                            </button>
                          </PermissionGuard>
                        </td>
                      ) : null}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
