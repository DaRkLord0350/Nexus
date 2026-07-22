'use client';

import { ArrowLeft, CheckCircle2, Plus, Trash2, XCircle } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError, FormInput } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import {
  addGoodsReceiptItem,
  cancelGoodsReceipt,
  completeGoodsReceipt,
  fetchGoodsReceipt,
  removeGoodsReceiptItem,
} from '@/lib/inventory/goods-receipts';
import type { GoodsReceiptDetail } from '@/lib/types';

export default function GoodsReceiptDetailPage() {
  const params = useParams<{ id: string }>();
  const receiptId = params.id;

  const [receipt, setReceipt] = useState<GoodsReceiptDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newProductId, setNewProductId] = useState('');
  const [newQuantity, setNewQuantity] = useState('1');
  const [newBatchNumber, setNewBatchNumber] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchGoodsReceipt(receiptId);
      setReceipt(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load goods receipt.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (receiptId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [receiptId]);

  const handleAddItem = async () => {
    if (!newProductId.trim()) return;
    try {
      await addGoodsReceiptItem(receiptId, {
        product_id: newProductId.trim(),
        quantity_received: Number(newQuantity),
        batch_number: newBatchNumber.trim() || undefined,
      });
      setNewProductId('');
      setNewQuantity('1');
      setNewBatchNumber('');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to add item.');
    }
  };

  const handleRemoveItem = async (itemId: string) => {
    try {
      await removeGoodsReceiptItem(receiptId, itemId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to remove item.');
    }
  };

  const handleComplete = async () => {
    if (!confirm('Complete this receipt? This will update inventory and cannot be undone.')) return;
    setActionLoading(true);
    try {
      await completeGoodsReceipt(receiptId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to complete goods receipt.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm('Cancel this goods receipt?')) return;
    setActionLoading(true);
    try {
      await cancelGoodsReceipt(receiptId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to cancel goods receipt.');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <SkeletonRows count={6} />;

  return (
    <div className="space-y-6">
      <Link href="/dashboard/inventory/goods-receipts" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
        <ArrowLeft size={14} /> Back to goods receipts
      </Link>

      <FormError message={error} />

      {!receipt ? (
        <EmptyState title="Goods receipt not found" />
      ) : (
        <>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{receipt.receipt_number}</h2>
                <p className="mt-1 text-sm capitalize text-slate-500 dark:text-slate-400">{receipt.status}</p>
              </div>
              <div className="flex gap-2">
                {receipt.status === 'draft' ? (
                  <PermissionGuard permission="inventory.goods_receipts.manage">
                    <button
                      type="button"
                      onClick={handleComplete}
                      disabled={actionLoading}
                      className="flex items-center gap-1.5 rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50"
                    >
                      <CheckCircle2 size={14} /> Complete
                    </button>
                  </PermissionGuard>
                ) : null}
                {receipt.status === 'draft' ? (
                  <PermissionGuard permission="inventory.goods_receipts.manage">
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
          </div>

          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Line items ({receipt.items.length})</h3>

          {receipt.status === 'draft' ? (
            <PermissionGuard permission="inventory.goods_receipts.create">
              <div className="grid grid-cols-[2fr_1fr_1fr_auto] gap-2 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
                <FormInput placeholder="Product ID" value={newProductId} onChange={(e) => setNewProductId(e.target.value)} />
                <FormInput type="number" min={1} placeholder="Qty" value={newQuantity} onChange={(e) => setNewQuantity(e.target.value)} />
                <FormInput placeholder="Batch # (optional)" value={newBatchNumber} onChange={(e) => setNewBatchNumber(e.target.value)} />
                <button type="button" onClick={handleAddItem} className="flex items-center justify-center gap-1.5 rounded-xl bg-cyan-500 px-3 text-sm font-semibold text-slate-950 hover:bg-cyan-400">
                  <Plus size={14} /> Add
                </button>
              </div>
            </PermissionGuard>
          ) : null}

          {receipt.items.length === 0 ? (
            <EmptyState title="No line items yet" />
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                  <tr>
                    <th className="px-4 py-3">Product</th>
                    <th className="px-4 py-3">Qty received</th>
                    <th className="px-4 py-3">Batch #</th>
                    <th className="px-4 py-3">Expiry</th>
                    {receipt.status === 'draft' ? <th className="px-4 py-3 text-right">Actions</th> : null}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {receipt.items.map((item) => (
                    <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                      <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{item.product_id.slice(0, 8)}…</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.quantity_received}</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.batch_number ?? '—'}</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.expiry_date ? new Date(item.expiry_date).toLocaleDateString() : '—'}</td>
                      {receipt.status === 'draft' ? (
                        <td className="px-4 py-3 text-right">
                          <PermissionGuard permission="inventory.goods_receipts.create">
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
