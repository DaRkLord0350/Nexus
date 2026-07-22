'use client';

import { ListTree, Pencil, Plus, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { AttributeFormModal } from '@/components/catalog/attribute-form-modal';
import { AttributeValueFormModal } from '@/components/catalog/attribute-value-form-modal';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError, FormInput } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import {
  createAttribute,
  createAttributeValue,
  deleteAttribute,
  deleteAttributeValue,
  fetchAttributes,
  fetchAttributeValues,
  updateAttribute,
  updateAttributeValue,
  type AttributeCreateInput,
  type AttributeValueCreateInput,
} from '@/lib/catalog/attributes';
import type { AttributeItem, AttributeValueItem } from '@/lib/types';

const PAGE_SIZE = 50;

export default function AttributesPage() {
  const [items, setItems] = useState<AttributeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState('');

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [values, setValues] = useState<AttributeValueItem[]>([]);
  const [valuesLoading, setValuesLoading] = useState(false);

  const [attributeFormTarget, setAttributeFormTarget] = useState<AttributeItem | null | undefined>(undefined);
  const [valueFormTarget, setValueFormTarget] = useState<AttributeValueItem | null | undefined>(undefined);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAttributes({ q: q || undefined, limit: PAGE_SIZE });
      setItems(data.items);
      if (!selectedId && data.items.length > 0) setSelectedId(data.items[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load attributes.');
    } finally {
      setLoading(false);
    }
  };

  const loadValues = async (attributeId: string) => {
    setValuesLoading(true);
    try {
      setValues(await fetchAttributeValues(attributeId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load attribute values.');
    } finally {
      setValuesLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (selectedId) loadValues(selectedId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  const handleSaveAttribute = async (data: AttributeCreateInput) => {
    if (attributeFormTarget) {
      await updateAttribute(attributeFormTarget.id, data);
    } else {
      const created = await createAttribute(data);
      setSelectedId(created.id);
    }
    await load();
  };

  const handleDeleteAttribute = async (attribute: AttributeItem) => {
    if (!confirm(`Delete "${attribute.name}" and all its values?`)) return;
    await deleteAttribute(attribute.id);
    if (selectedId === attribute.id) setSelectedId(null);
    await load();
  };

  const handleSaveValue = async (data: AttributeValueCreateInput) => {
    if (!selectedId) return;
    if (valueFormTarget) {
      await updateAttributeValue(selectedId, valueFormTarget.id, data);
    } else {
      await createAttributeValue(selectedId, data);
    }
    await loadValues(selectedId);
  };

  const handleDeleteValue = async (value: AttributeValueItem) => {
    if (!selectedId || !confirm(`Delete value "${value.value}"?`)) return;
    await deleteAttributeValue(selectedId, value.id);
    await loadValues(selectedId);
  };

  const selectedAttribute = items.find((i) => i.id === selectedId) ?? null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Attributes</h2>
        <PermissionGuard permission="catalog.attributes.manage">
          <button
            type="button"
            onClick={() => setAttributeFormTarget(null)}
            className="flex items-center gap-2 rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400"
          >
            <Plus size={16} />
            New attribute
          </button>
        </PermissionGuard>
      </div>

      <FormError message={error} />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
        <div className="space-y-3">
          <FormInput
            placeholder="Search attributes…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') load(); }}
          />
          {loading ? (
            <SkeletonRows count={5} />
          ) : items.length === 0 ? (
            <EmptyState icon={ListTree} title="No attributes found" description="Create your first attribute (e.g. Color, Size)." />
          ) : (
            <div className="divide-y divide-slate-100 rounded-2xl border border-slate-200 dark:divide-slate-800 dark:border-slate-800">
              {items.map((attribute) => (
                <button
                  key={attribute.id}
                  type="button"
                  onClick={() => setSelectedId(attribute.id)}
                  className={`flex w-full items-center justify-between px-4 py-3 text-left text-sm transition ${
                    selectedId === attribute.id
                      ? 'bg-cyan-500/10 text-cyan-700 dark:text-cyan-300'
                      : 'bg-white text-slate-700 hover:bg-slate-50 dark:bg-slate-900/40 dark:text-slate-200 dark:hover:bg-slate-800/60'
                  }`}
                >
                  <span>
                    <span className="font-medium">{attribute.name}</span>
                    <span className="ml-2 text-xs text-slate-400">{attribute.input_type}</span>
                    {!attribute.is_active ? <span className="ml-2 text-xs text-amber-500">inactive</span> : null}
                  </span>
                  <PermissionGuard permission="catalog.attributes.manage">
                    <span className="flex gap-1.5">
                      <span
                        role="button"
                        tabIndex={0}
                        onClick={(e) => { e.stopPropagation(); setAttributeFormTarget(attribute); }}
                        className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800 dark:hover:text-white"
                      >
                        <Pencil size={14} />
                      </span>
                      <span
                        role="button"
                        tabIndex={0}
                        onClick={(e) => { e.stopPropagation(); handleDeleteAttribute(attribute); }}
                        className="rounded-lg p-1 text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10"
                      >
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
          {!selectedAttribute ? (
            <EmptyState title="Select an attribute" description="Choose an attribute on the left to manage its values." />
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-slate-900 dark:text-white">{selectedAttribute.name} values</h3>
                <PermissionGuard permission="catalog.attributes.manage">
                  <button
                    type="button"
                    onClick={() => setValueFormTarget(null)}
                    className="rounded-xl bg-cyan-500 px-3 py-1.5 text-xs font-semibold text-slate-950 transition hover:bg-cyan-400"
                  >
                    Add value
                  </button>
                </PermissionGuard>
              </div>

              {valuesLoading ? (
                <SkeletonRows count={3} />
              ) : values.length === 0 ? (
                <EmptyState title="No values yet" description="Add the first value for this attribute." />
              ) : (
                <div className="space-y-2">
                  {values.map((value) => (
                    <div key={value.id} className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-950/60">
                      <span className="flex items-center gap-2 text-slate-800 dark:text-slate-100">
                        {value.color_hex ? (
                          <span className="h-4 w-4 rounded-full border border-slate-300 dark:border-slate-600" style={{ backgroundColor: value.color_hex }} />
                        ) : null}
                        {value.value}
                        {!value.is_active ? <span className="text-xs text-amber-500">inactive</span> : null}
                      </span>
                      <PermissionGuard permission="catalog.attributes.manage">
                        <div className="flex gap-2">
                          <button type="button" onClick={() => setValueFormTarget(value)} className="rounded-lg p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white">
                            <Pencil size={14} />
                          </button>
                          <button type="button" onClick={() => handleDeleteValue(value)} className="rounded-lg p-1 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10">
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </PermissionGuard>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {attributeFormTarget !== undefined ? (
        <AttributeFormModal attribute={attributeFormTarget} onSubmit={handleSaveAttribute} onClose={() => setAttributeFormTarget(undefined)} />
      ) : null}
      {valueFormTarget !== undefined && selectedId ? (
        <AttributeValueFormModal value={valueFormTarget} onSubmit={handleSaveValue} onClose={() => setValueFormTarget(undefined)} />
      ) : null}
    </div>
  );
}
