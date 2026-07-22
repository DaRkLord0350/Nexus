'use client';

import { QrCode, Star, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { BarcodeFormModal } from '@/components/inventory/barcode-form-modal';
import { BarcodeRender } from '@/components/inventory/barcode-render';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError, FormInput } from '@/components/ui/form';
import { SkeletonGrid } from '@/components/ui/skeleton';
import {
  bulkDeleteBarcodes,
  createBarcode,
  deleteBarcode,
  fetchBarcodes,
  type BarcodeCreateInput,
} from '@/lib/inventory/barcodes';
import type { BarcodeItem } from '@/lib/types';

const PAGE_SIZE = 24;

export default function BarcodeCenterPage() {
  const [items, setItems] = useState<BarcodeItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState('');
  const [formatFilter, setFormatFilter] = useState('');
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [showForm, setShowForm] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchBarcodes({ q: q || undefined, format: formatFilter || undefined, limit: PAGE_SIZE, offset });
      setItems(data.items);
      setTotal(data.total);
      setSelected(new Set());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load barcodes.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offset]);

  const applyFilters = () => {
    setOffset(0);
    load();
  };

  const handleSave = async (data: BarcodeCreateInput) => {
    await createBarcode(data);
    await load();
  };

  const handleDelete = async (barcode: BarcodeItem) => {
    if (!confirm(`Delete barcode "${barcode.value}"?`)) return;
    try {
      await deleteBarcode(barcode.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete barcode.');
    }
  };

  const handleBulkDelete = async () => {
    if (selected.size === 0) return;
    if (!confirm(`Delete ${selected.size} selected barcode(s)?`)) return;
    try {
      await bulkDeleteBarcodes(Array.from(selected));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete selected barcodes.');
    }
  };

  const toggleSelected = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Barcode Center</h2>
        <PermissionGuard permission="inventory.barcodes.manage">
          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400"
          >
            New barcode
          </button>
        </PermissionGuard>
      </div>

      <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60 sm:grid-cols-3">
        <FormInput placeholder="Search by value…" value={q} onChange={(e) => setQ(e.target.value)} />
        <select
          value={formatFilter}
          onChange={(e) => setFormatFilter(e.target.value)}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
        >
          <option value="">All formats</option>
          <option value="code128">Code128</option>
          <option value="ean13">EAN13</option>
          <option value="upc">UPC</option>
          <option value="qr">QR</option>
        </select>
        <button
          type="button"
          onClick={applyFilters}
          className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400"
        >
          Apply filters
        </button>
      </div>

      <FormError message={error} />

      {selected.size > 0 ? (
        <PermissionGuard permission="inventory.barcodes.manage">
          <div className="flex items-center justify-between rounded-xl border border-cyan-300 bg-cyan-50 px-4 py-2.5 text-sm dark:border-cyan-700 dark:bg-cyan-500/10">
            <span className="text-cyan-800 dark:text-cyan-200">{selected.size} selected</span>
            <button type="button" onClick={handleBulkDelete} className="flex items-center gap-1.5 font-semibold text-red-600 dark:text-red-400">
              <Trash2 size={14} /> Delete selected
            </button>
          </div>
        </PermissionGuard>
      ) : null}

      {loading ? (
        <SkeletonGrid count={8} />
      ) : items.length === 0 ? (
        <EmptyState icon={QrCode} title="No barcodes found" description="Generate barcodes and QR codes for products and variants." />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4">
          {items.map((item) => (
            <div key={item.id} className="flex flex-col items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
              <div className="flex w-full items-center justify-between">
                <input type="checkbox" checked={selected.has(item.id)} onChange={() => toggleSelected(item.id)} />
                <div className="flex items-center gap-2">
                  {item.is_primary ? <Star size={14} className="text-amber-500" /> : null}
                  <span className="text-xs uppercase tracking-wide text-slate-400">{item.format}</span>
                </div>
              </div>
              <BarcodeRender value={item.value} format={item.format} label={item.value} />
              <div className="text-center text-xs text-slate-500 dark:text-slate-400">
                {item.product_id ? `Product: ${item.product_id.slice(0, 8)}…` : `Variant: ${item.variant_id?.slice(0, 8)}…`}
              </div>
              <PermissionGuard permission="inventory.barcodes.manage">
                <button type="button" onClick={() => handleDelete(item)} className="flex items-center gap-1 text-xs font-medium text-red-500 hover:text-red-600 dark:text-red-400">
                  <Trash2 size={12} /> Delete
                </button>
              </PermissionGuard>
            </div>
          ))}
        </div>
      )}

      {total > 0 ? (
        <div className="flex items-center justify-between text-sm text-slate-500 dark:text-slate-400">
          <span>Page {currentPage} of {totalPages} ({total} total)</span>
          <div className="flex gap-2">
            <button type="button" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))} className="rounded-lg border border-slate-300 px-3 py-1.5 font-medium text-slate-700 disabled:opacity-40 dark:border-slate-700 dark:text-slate-200">
              Previous
            </button>
            <button type="button" disabled={offset + PAGE_SIZE >= total} onClick={() => setOffset(offset + PAGE_SIZE)} className="rounded-lg border border-slate-300 px-3 py-1.5 font-medium text-slate-700 disabled:opacity-40 dark:border-slate-700 dark:text-slate-200">
              Next
            </button>
          </div>
        </div>
      ) : null}

      {showForm ? <BarcodeFormModal onSubmit={handleSave} onClose={() => setShowForm(false)} /> : null}
    </div>
  );
}
