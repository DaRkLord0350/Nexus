'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { ReorderRuleCreateInput, ReorderRuleUpdateInput } from '@/lib/inventory/reorder-rules';
import type { ReorderRuleItem, WarehouseItem } from '@/lib/types';

interface ReorderRuleFormModalProps {
  rule?: ReorderRuleItem | null;
  warehouses: WarehouseItem[];
  onSubmit: (data: ReorderRuleCreateInput | ReorderRuleUpdateInput) => Promise<void>;
  onClose: () => void;
}

export function ReorderRuleFormModal({ rule, warehouses, onSubmit, onClose }: ReorderRuleFormModalProps) {
  const [productId, setProductId] = useState(rule?.product_id ?? '');
  const [warehouseId, setWarehouseId] = useState(rule?.warehouse_id ?? warehouses[0]?.id ?? '');
  const [minimumStock, setMinimumStock] = useState(rule ? String(rule.minimum_stock) : '');
  const [maximumStock, setMaximumStock] = useState(rule?.maximum_stock != null ? String(rule.maximum_stock) : '');
  const [reorderQuantity, setReorderQuantity] = useState(rule ? String(rule.reorder_quantity) : '');
  const [supplierName, setSupplierName] = useState(rule?.supplier_name ?? '');
  const [leadTimeDays, setLeadTimeDays] = useState(rule?.lead_time_days != null ? String(rule.lead_time_days) : '');
  const [isActive, setIsActive] = useState(rule?.is_active ?? true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!rule && (!productId.trim() || !warehouseId)) return;
    setLoading(true);
    setError(null);
    try {
      if (rule) {
        await onSubmit({
          minimum_stock: minimumStock ? Number(minimumStock) : undefined,
          maximum_stock: maximumStock ? Number(maximumStock) : undefined,
          reorder_quantity: reorderQuantity ? Number(reorderQuantity) : undefined,
          supplier_name: supplierName.trim() || undefined,
          lead_time_days: leadTimeDays ? Number(leadTimeDays) : undefined,
          is_active: isActive,
        });
      } else {
        await onSubmit({
          product_id: productId.trim(),
          warehouse_id: warehouseId,
          minimum_stock: Number(minimumStock),
          maximum_stock: maximumStock ? Number(maximumStock) : undefined,
          reorder_quantity: Number(reorderQuantity),
          supplier_name: supplierName.trim() || undefined,
          lead_time_days: leadTimeDays ? Number(leadTimeDays) : undefined,
          is_active: isActive,
        });
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save reorder rule.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={rule ? 'Edit reorder rule' : 'New reorder rule'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormError message={error} />

        {!rule ? (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <FormField label="Product ID" htmlFor="rr-product" />
              <FormInput id="rr-product" autoFocus value={productId} onChange={(e) => setProductId(e.target.value)} required />
            </div>
            <div>
              <FormField label="Warehouse" htmlFor="rr-warehouse" />
              <select
                id="rr-warehouse"
                value={warehouseId}
                onChange={(e) => setWarehouseId(e.target.value)}
                required
                className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
              >
                <option value="">Select…</option>
                {warehouses.map((w) => (
                  <option key={w.id} value={w.id}>{w.name}</option>
                ))}
              </select>
            </div>
          </div>
        ) : null}

        <div className="grid grid-cols-3 gap-4">
          <div>
            <FormField label="Min stock" htmlFor="rr-min" />
            <FormInput id="rr-min" type="number" min={0} value={minimumStock} onChange={(e) => setMinimumStock(e.target.value)} required />
          </div>
          <div>
            <FormField label="Max stock" htmlFor="rr-max" />
            <FormInput id="rr-max" type="number" min={0} value={maximumStock} onChange={(e) => setMaximumStock(e.target.value)} />
          </div>
          <div>
            <FormField label="Reorder qty" htmlFor="rr-qty" />
            <FormInput id="rr-qty" type="number" min={1} value={reorderQuantity} onChange={(e) => setReorderQuantity(e.target.value)} required />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Supplier" htmlFor="rr-supplier" />
            <FormInput id="rr-supplier" value={supplierName} onChange={(e) => setSupplierName(e.target.value)} />
          </div>
          <div>
            <FormField label="Lead time (days)" htmlFor="rr-lead-time" />
            <FormInput id="rr-lead-time" type="number" min={0} value={leadTimeDays} onChange={(e) => setLeadTimeDays(e.target.value)} />
          </div>
        </div>

        <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
          <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
          Active
        </label>

        <FormButton type="submit" loading={loading}>
          {rule ? 'Save changes' : 'Create reorder rule'}
        </FormButton>
      </form>
    </Modal>
  );
}
