'use client';

import { Layers3, Pencil, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { ProductTypeFormModal } from '@/components/catalog/product-type-form-modal';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { SkeletonRows } from '@/components/ui/skeleton';
import { fetchAttributes } from '@/lib/catalog/attributes';
import {
  createProductType,
  deleteProductType,
  fetchProductTypeAttributes,
  fetchProductTypes,
  setProductTypeAttributes,
  updateProductType,
  type ProductTypeCreateInput,
} from '@/lib/catalog/product-types';
import type { AttributeItem, ProductTypeAttributeItem, ProductTypeItem } from '@/lib/types';

export default function ProductTypesPage() {
  const [items, setItems] = useState<ProductTypeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [assignedAttributes, setAssignedAttributes] = useState<ProductTypeAttributeItem[]>([]);
  const [allAttributes, setAllAttributes] = useState<AttributeItem[]>([]);
  const [selectedAttributeIds, setSelectedAttributeIds] = useState<Set<string>>(new Set());
  const [requiredAttributeIds, setRequiredAttributeIds] = useState<Set<string>>(new Set());
  const [savingAttributes, setSavingAttributes] = useState(false);

  const [formTarget, setFormTarget] = useState<ProductTypeItem | null | undefined>(undefined);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [typesData, attributesData] = await Promise.all([
        fetchProductTypes(),
        fetchAttributes({ isVariantAttribute: true, isActive: true, limit: 100 }),
      ]);
      setItems(typesData.items);
      setAllAttributes(attributesData.items);
      if (!selectedId && typesData.items.length > 0) setSelectedId(typesData.items[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load product types.');
    } finally {
      setLoading(false);
    }
  };

  const loadAssignedAttributes = async (productTypeId: string) => {
    const attributes = await fetchProductTypeAttributes(productTypeId);
    setAssignedAttributes(attributes);
    setSelectedAttributeIds(new Set(attributes.map((a) => a.attribute_id)));
    setRequiredAttributeIds(new Set(attributes.filter((a) => a.is_required).map((a) => a.attribute_id)));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (selectedId) loadAssignedAttributes(selectedId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  const handleSave = async (data: ProductTypeCreateInput) => {
    if (formTarget) {
      await updateProductType(formTarget.id, data);
    } else {
      const created = await createProductType(data);
      setSelectedId(created.id);
    }
    await load();
  };

  const handleDelete = async (productType: ProductTypeItem) => {
    if (!confirm(`Delete "${productType.name}"?`)) return;
    await deleteProductType(productType.id);
    if (selectedId === productType.id) setSelectedId(null);
    await load();
  };

  const toggleAttribute = (attributeId: string) => {
    setSelectedAttributeIds((prev) => {
      const next = new Set(prev);
      if (next.has(attributeId)) {
        next.delete(attributeId);
        setRequiredAttributeIds((req) => {
          const nextReq = new Set(req);
          nextReq.delete(attributeId);
          return nextReq;
        });
      } else {
        next.add(attributeId);
      }
      return next;
    });
  };

  const toggleRequired = (attributeId: string) => {
    setRequiredAttributeIds((prev) => {
      const next = new Set(prev);
      if (next.has(attributeId)) next.delete(attributeId); else next.add(attributeId);
      return next;
    });
  };

  const handleSaveAttributes = async () => {
    if (!selectedId) return;
    setSavingAttributes(true);
    try {
      const attributes = Array.from(selectedAttributeIds).map((attribute_id, index) => ({
        attribute_id,
        is_required: requiredAttributeIds.has(attribute_id),
        sort_order: index,
      }));
      await setProductTypeAttributes(selectedId, attributes);
      await loadAssignedAttributes(selectedId);
    } finally {
      setSavingAttributes(false);
    }
  };

  const selectedType = items.find((i) => i.id === selectedId) ?? null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Product Types</h2>
        <PermissionGuard permission="catalog.product_types.manage">
          <button type="button" onClick={() => setFormTarget(null)} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400">
            New product type
          </button>
        </PermissionGuard>
      </div>

      {error ? <p className="text-sm text-red-600 dark:text-red-400">{error}</p> : null}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
        <div className="space-y-3">
          {loading ? (
            <SkeletonRows count={4} />
          ) : items.length === 0 ? (
            <EmptyState icon={Layers3} title="No product types found" description="Create a product type (e.g. T-Shirt) to define which attributes apply." />
          ) : (
            <div className="divide-y divide-slate-100 rounded-2xl border border-slate-200 dark:divide-slate-800 dark:border-slate-800">
              {items.map((productType) => (
                <button
                  key={productType.id}
                  type="button"
                  onClick={() => setSelectedId(productType.id)}
                  className={`flex w-full items-center justify-between px-4 py-3 text-left text-sm transition ${
                    selectedId === productType.id
                      ? 'bg-cyan-500/10 text-cyan-700 dark:text-cyan-300'
                      : 'bg-white text-slate-700 hover:bg-slate-50 dark:bg-slate-900/40 dark:text-slate-200 dark:hover:bg-slate-800/60'
                  }`}
                >
                  <span>
                    <span className="font-medium">{productType.name}</span>
                    {!productType.is_active ? <span className="ml-2 text-xs text-amber-500">inactive</span> : null}
                  </span>
                  <PermissionGuard permission="catalog.product_types.manage">
                    <span className="flex gap-1.5">
                      <span role="button" tabIndex={0} onClick={(e) => { e.stopPropagation(); setFormTarget(productType); }} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800 dark:hover:text-white">
                        <Pencil size={14} />
                      </span>
                      <span role="button" tabIndex={0} onClick={(e) => { e.stopPropagation(); handleDelete(productType); }} className="rounded-lg p-1 text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10">
                        <Trash2 size={14} />
                      </span>
                    </span>
                  </PermissionGuard>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-slate-200 p-4 dark:border-slate-800">
          {!selectedType ? (
            <EmptyState title="Select a product type" description="Choose a product type on the left to configure its attributes." />
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-slate-900 dark:text-white">{selectedType.name} attributes</h3>
                <PermissionGuard permission="catalog.product_types.manage">
                  <button type="button" onClick={handleSaveAttributes} disabled={savingAttributes} className="rounded-xl bg-cyan-500 px-3 py-1.5 text-xs font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50">
                    {savingAttributes ? 'Saving…' : 'Save attributes'}
                  </button>
                </PermissionGuard>
              </div>

              {allAttributes.length === 0 ? (
                <EmptyState title="No variant attributes yet" description="Create attributes first (e.g. Color, Size) to assign them here." />
              ) : (
                <div className="space-y-2">
                  {allAttributes.map((attribute) => (
                    <div key={attribute.id} className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-950/60">
                      <label className="flex items-center gap-2 text-slate-800 dark:text-slate-100">
                        <input type="checkbox" checked={selectedAttributeIds.has(attribute.id)} onChange={() => toggleAttribute(attribute.id)} />
                        {attribute.name}
                      </label>
                      {selectedAttributeIds.has(attribute.id) ? (
                        <label className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
                          <input type="checkbox" checked={requiredAttributeIds.has(attribute.id)} onChange={() => toggleRequired(attribute.id)} />
                          Required
                        </label>
                      ) : null}
                    </div>
                  ))}
                </div>
              )}
              {assignedAttributes.length === 0 && allAttributes.length > 0 ? (
                <p className="text-xs text-slate-400 dark:text-slate-500">No attributes assigned yet.</p>
              ) : null}
            </div>
          )}
        </div>
      </div>

      {formTarget !== undefined ? (
        <ProductTypeFormModal productType={formTarget} onSubmit={handleSave} onClose={() => setFormTarget(undefined)} />
      ) : null}
    </div>
  );
}
