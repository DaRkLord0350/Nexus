'use client';

import { Plus, Trash2 } from 'lucide-react';
import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { PurchaseOrderCreateInput, PurchaseOrderLineItemInput } from '@/lib/inventory/purchase-orders';
import type { WarehouseItem } from '@/lib/types';

interface PurchaseOrderFormModalProps {
  warehouses: WarehouseItem[];
  onSubmit: (data: PurchaseOrderCreateInput) => Promise<void>;
  onClose: () => void;
}

interface DraftItem extends PurchaseOrderLineItemInput {
  key: string;
}

export function PurchaseOrderFormModal({ warehouses, onSubmit, onClose }: PurchaseOrderFormModalProps) {
  const [supplierName, setSupplierName] = useState('');
  const [supplierEmail, setSupplierEmail] = useState('');
  const [warehouseId, setWarehouseId] = useState(warehouses[0]?.id ?? '');
  const [expectedDate, setExpectedDate] = useState('');
  const [taxAmount, setTaxAmount] = useState('0');
  const [shippingAmount, setShippingAmount] = useState('0');
  const [items, setItems] = useState<DraftItem[]>([{ key: crypto.randomUUID(), product_id: '', quantity_ordered: 1, unit_cost: 0 }]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addItemRow = () => {
    setItems((prev) => [...prev, { key: crypto.randomUUID(), product_id: '', quantity_ordered: 1, unit_cost: 0 }]);
  };

  const removeItemRow = (key: string) => {
    setItems((prev) => prev.filter((item) => item.key !== key));
  };

  const updateItem = (key: string, patch: Partial<DraftItem>) => {
    setItems((prev) => prev.map((item) => (item.key === key ? { ...item, ...patch } : item)));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!supplierName.trim() || !warehouseId) return;
    setLoading(true);
    setError(null);
    try {
      const validItems = items.filter((item) => item.product_id.trim() && item.quantity_ordered > 0);
      await onSubmit({
        supplier_name: supplierName.trim(),
        supplier_email: supplierEmail.trim() || undefined,
        warehouse_id: warehouseId,
        expected_date: expectedDate || undefined,
        tax_amount: Number(taxAmount) || 0,
        shipping_amount: Number(shippingAmount) || 0,
        items: validItems.map(({ key, ...rest }) => rest),
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create purchase order.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title="New purchase order" onClose={onClose}>
      <form onSubmit={handleSubmit} className="max-h-[75vh] space-y-4 overflow-y-auto pr-1">
        <FormError message={error} />

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Supplier name" htmlFor="po-supplier" />
            <FormInput id="po-supplier" autoFocus value={supplierName} onChange={(e) => setSupplierName(e.target.value)} required />
          </div>
          <div>
            <FormField label="Supplier email" htmlFor="po-supplier-email" />
            <FormInput id="po-supplier-email" type="email" value={supplierEmail} onChange={(e) => setSupplierEmail(e.target.value)} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Warehouse" htmlFor="po-warehouse" />
            <select
              id="po-warehouse"
              value={warehouseId}
              onChange={(e) => setWarehouseId(e.target.value)}
              required
              className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
            >
              <option value="">Select warehouse…</option>
              {warehouses.map((w) => (
                <option key={w.id} value={w.id}>{w.name}</option>
              ))}
            </select>
          </div>
          <div>
            <FormField label="Expected date" htmlFor="po-expected" />
            <FormInput id="po-expected" type="date" value={expectedDate} onChange={(e) => setExpectedDate(e.target.value)} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Tax amount" htmlFor="po-tax" />
            <FormInput id="po-tax" type="number" step="0.01" min={0} value={taxAmount} onChange={(e) => setTaxAmount(e.target.value)} />
          </div>
          <div>
            <FormField label="Shipping amount" htmlFor="po-shipping" />
            <FormInput id="po-shipping" type="number" step="0.01" min={0} value={shippingAmount} onChange={(e) => setShippingAmount(e.target.value)} />
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <FormField label="Line items" htmlFor="po-items" />
            <button type="button" onClick={addItemRow} className="flex items-center gap-1 text-xs font-semibold text-cyan-600 dark:text-cyan-400">
              <Plus size={12} /> Add item
            </button>
          </div>
          {items.map((item) => (
            <div key={item.key} className="grid grid-cols-[2fr_1fr_1fr_auto] gap-2">
              <FormInput placeholder="Product ID" value={item.product_id} onChange={(e) => updateItem(item.key, { product_id: e.target.value })} />
              <FormInput type="number" min={1} placeholder="Qty" value={item.quantity_ordered} onChange={(e) => updateItem(item.key, { quantity_ordered: Number(e.target.value) })} />
              <FormInput type="number" min={0} step="0.01" placeholder="Unit cost" value={item.unit_cost} onChange={(e) => updateItem(item.key, { unit_cost: Number(e.target.value) })} />
              <button type="button" onClick={() => removeItemRow(item.key)} className="rounded-lg p-2 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>

        <FormButton type="submit" loading={loading}>
          Create purchase order
        </FormButton>
      </form>
    </Modal>
  );
}
