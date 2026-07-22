'use client';

import { useEffect, useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import { fetchAttributes, fetchAttributeValues } from '@/lib/catalog/attributes';
import type { VariantCreateInput } from '@/lib/catalog/variants';
import type { AttributeItem, AttributeValueItem, VariantItem } from '@/lib/types';

interface VariantFormModalProps {
  variant?: VariantItem | null;
  onSubmit: (data: VariantCreateInput) => Promise<void>;
  onClose: () => void;
}

export function VariantFormModal({ variant, onSubmit, onClose }: VariantFormModalProps) {
  const [sku, setSku] = useState(variant?.sku ?? '');
  const [barcode, setBarcode] = useState(variant?.barcode ?? '');
  const [weight, setWeight] = useState(variant?.weight ?? undefined);
  const [status, setStatus] = useState(variant?.status ?? 'active');
  const [isDefault, setIsDefault] = useState(variant?.is_default ?? false);
  const [selectedValueIds, setSelectedValueIds] = useState<Set<string>>(new Set(variant?.attribute_values.map((v) => v.id) ?? []));

  const [attributes, setAttributes] = useState<AttributeItem[]>([]);
  const [valuesByAttribute, setValuesByAttribute] = useState<Record<string, AttributeValueItem[]>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAttributes({ isVariantAttribute: true, isActive: true, limit: 100 }).then(async (data) => {
      setAttributes(data.items);
      const entries = await Promise.all(data.items.map(async (attr) => [attr.id, await fetchAttributeValues(attr.id)] as const));
      setValuesByAttribute(Object.fromEntries(entries));
    }).catch(() => setAttributes([]));
  }, []);

  const toggleValue = (valueId: string) => {
    setSelectedValueIds((prev) => {
      const next = new Set(prev);
      if (next.has(valueId)) next.delete(valueId); else next.add(valueId);
      return next;
    });
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!sku.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        sku: sku.trim(),
        barcode: barcode.trim() || undefined,
        weight,
        status,
        is_default: isDefault,
        attribute_value_ids: Array.from(selectedValueIds),
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save variant.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={variant ? 'Edit variant' : 'New variant'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="max-h-[70vh] space-y-4 overflow-y-auto pr-1">
        <FormError message={error} />

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="SKU" htmlFor="var-sku" />
            <FormInput id="var-sku" autoFocus value={sku} onChange={(e) => setSku(e.target.value)} required />
          </div>
          <div>
            <FormField label="Barcode" htmlFor="var-barcode" />
            <FormInput id="var-barcode" value={barcode} onChange={(e) => setBarcode(e.target.value)} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Weight" htmlFor="var-weight" />
            <FormInput id="var-weight" type="number" value={weight ?? ''} onChange={(e) => setWeight(e.target.value ? Number(e.target.value) : undefined)} />
          </div>
          <div>
            <FormField label="Status" htmlFor="var-status" />
            <select id="var-status" value={status} onChange={(e) => setStatus(e.target.value as 'active' | 'archived')} className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
              <option value="active">Active</option>
              <option value="archived">Archived</option>
            </select>
          </div>
        </div>

        <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
          <input type="checkbox" checked={isDefault} onChange={(e) => setIsDefault(e.target.checked)} />
          Default variant
        </label>

        {attributes.length > 0 ? (
          <div className="space-y-3 rounded-xl border border-slate-200 p-3 dark:border-slate-800">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Attribute values</p>
            {attributes.map((attribute) => (
              <div key={attribute.id}>
                <p className="mb-1 text-xs font-medium text-slate-600 dark:text-slate-300">{attribute.name}</p>
                <div className="flex flex-wrap gap-2">
                  {(valuesByAttribute[attribute.id] ?? []).map((value) => (
                    <label
                      key={value.id}
                      className={`cursor-pointer rounded-full border px-2.5 py-1 text-xs ${
                        selectedValueIds.has(value.id)
                          ? 'border-cyan-500 bg-cyan-500/10 text-cyan-700 dark:text-cyan-300'
                          : 'border-slate-300 text-slate-600 dark:border-slate-700 dark:text-slate-300'
                      }`}
                    >
                      <input type="checkbox" className="hidden" checked={selectedValueIds.has(value.id)} onChange={() => toggleValue(value.id)} />
                      {value.value}
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : null}

        <FormButton type="submit" loading={loading}>
          {variant ? 'Save changes' : 'Create variant'}
        </FormButton>
      </form>
    </Modal>
  );
}
