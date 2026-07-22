'use client';

import { ArrowLeft, Package, Plus, Send, Trash2, XCircle } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError, FormInput } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import {
  addTransferItem,
  cancelTransfer,
  fetchTransfer,
  packTransfer,
  receiveTransfer,
  removeTransferItem,
  shipTransfer,
} from '@/lib/inventory/transfers';
import type { StockTransferDetail } from '@/lib/types';

export default function TransferDetailPage() {
  const params = useParams<{ id: string }>();
  const transferId = params.id;

  const [transfer, setTransfer] = useState<StockTransferDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newProductId, setNewProductId] = useState('');
  const [newQuantity, setNewQuantity] = useState('1');
  const [actionLoading, setActionLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchTransfer(transferId);
      setTransfer(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load stock transfer.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (transferId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [transferId]);

  const handleAddItem = async () => {
    if (!newProductId.trim()) return;
    try {
      await addTransferItem(transferId, { product_id: newProductId.trim(), quantity_requested: Number(newQuantity) });
      setNewProductId('');
      setNewQuantity('1');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to add item.');
    }
  };

  const handleRemoveItem = async (itemId: string) => {
    try {
      await removeTransferItem(transferId, itemId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to remove item.');
    }
  };

  const runAction = async (action: () => Promise<unknown>, failureMessage: string) => {
    setActionLoading(true);
    try {
      await action();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : failureMessage);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <SkeletonRows count={6} />;

  return (
    <div className="space-y-6">
      <Link href="/dashboard/inventory/transfers" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
        <ArrowLeft size={14} /> Back to transfers
      </Link>

      <FormError message={error} />

      {!transfer ? (
        <EmptyState title="Stock transfer not found" />
      ) : (
        <>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{transfer.transfer_number}</h2>
                <p className="mt-1 text-sm capitalize text-slate-500 dark:text-slate-400">{transfer.status}</p>
              </div>
              <div className="flex gap-2">
                {transfer.status === 'draft' ? (
                  <PermissionGuard permission="inventory.transfers.manage">
                    <button
                      type="button"
                      onClick={() => runAction(() => packTransfer(transferId), 'Unable to pack transfer.')}
                      disabled={actionLoading}
                      className="flex items-center gap-1.5 rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50"
                    >
                      <Package size={14} /> Pack
                    </button>
                  </PermissionGuard>
                ) : null}
                {transfer.status === 'packed' ? (
                  <PermissionGuard permission="inventory.transfers.manage">
                    <button
                      type="button"
                      onClick={() => runAction(() => shipTransfer(transferId), 'Unable to ship transfer.')}
                      disabled={actionLoading}
                      className="flex items-center gap-1.5 rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50"
                    >
                      <Send size={14} /> Ship
                    </button>
                  </PermissionGuard>
                ) : null}
                {transfer.status === 'shipped' ? (
                  <PermissionGuard permission="inventory.transfers.manage">
                    <button
                      type="button"
                      onClick={() => runAction(() => receiveTransfer(transferId), 'Unable to receive transfer.')}
                      disabled={actionLoading}
                      className="flex items-center gap-1.5 rounded-xl bg-emerald-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-emerald-400 disabled:opacity-50"
                    >
                      <Package size={14} /> Receive
                    </button>
                  </PermissionGuard>
                ) : null}
                {transfer.status === 'draft' || transfer.status === 'packed' ? (
                  <PermissionGuard permission="inventory.transfers.manage">
                    <button
                      type="button"
                      onClick={() => runAction(() => cancelTransfer(transferId), 'Unable to cancel transfer.')}
                      disabled={actionLoading}
                      className="flex items-center gap-1.5 rounded-xl border border-red-300 px-3.5 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50 dark:border-red-500/40 dark:text-red-400 dark:hover:bg-red-500/10"
                    >
                      <XCircle size={14} /> Cancel
                    </button>
                  </PermissionGuard>
                ) : null}
              </div>
            </div>
          </div>

          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Line items ({transfer.items.length})</h3>

          {transfer.status === 'draft' ? (
            <PermissionGuard permission="inventory.transfers.create">
              <div className="grid grid-cols-[2fr_1fr_auto] gap-2 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
                <FormInput placeholder="Product ID" value={newProductId} onChange={(e) => setNewProductId(e.target.value)} />
                <FormInput type="number" min={1} placeholder="Qty" value={newQuantity} onChange={(e) => setNewQuantity(e.target.value)} />
                <button type="button" onClick={handleAddItem} className="flex items-center justify-center gap-1.5 rounded-xl bg-cyan-500 px-3 text-sm font-semibold text-slate-950 hover:bg-cyan-400">
                  <Plus size={14} /> Add
                </button>
              </div>
            </PermissionGuard>
          ) : null}

          {transfer.items.length === 0 ? (
            <EmptyState title="No line items yet" />
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                  <tr>
                    <th className="px-4 py-3">Product</th>
                    <th className="px-4 py-3">Requested</th>
                    <th className="px-4 py-3">Shipped</th>
                    <th className="px-4 py-3">Received</th>
                    {transfer.status === 'draft' ? <th className="px-4 py-3 text-right">Actions</th> : null}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {transfer.items.map((item) => (
                    <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                      <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{item.product_id.slice(0, 8)}…</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.quantity_requested}</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.quantity_shipped}</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.quantity_received}</td>
                      {transfer.status === 'draft' ? (
                        <td className="px-4 py-3 text-right">
                          <PermissionGuard permission="inventory.transfers.create">
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
