'use client';

import { ListPlus, Pencil, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { CustomFieldDefinitionFormModal } from '@/components/catalog/custom-field-definition-form-modal';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { SkeletonRows } from '@/components/ui/skeleton';
import {
  createCustomFieldDefinition,
  deleteCustomFieldDefinition,
  fetchCustomFieldDefinitions,
  updateCustomFieldDefinition,
  type CustomFieldDefinitionCreateInput,
} from '@/lib/catalog/custom-fields';
import type { CustomFieldDefinitionItem, CustomFieldEntityType } from '@/lib/types';

const ENTITY_TYPES: { value: CustomFieldEntityType; label: string }[] = [
  { value: 'product', label: 'Products' },
  { value: 'variant', label: 'Variants' },
  { value: 'category', label: 'Categories' },
  { value: 'brand', label: 'Brands' },
  { value: 'collection', label: 'Collections' },
];

export default function CustomFieldsPage() {
  const [entityType, setEntityType] = useState<CustomFieldEntityType>('product');
  const [items, setItems] = useState<CustomFieldDefinitionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formTarget, setFormTarget] = useState<CustomFieldDefinitionItem | null | undefined>(undefined);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCustomFieldDefinitions(entityType);
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load custom fields.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entityType]);

  const handleSave = async (data: CustomFieldDefinitionCreateInput) => {
    if (formTarget) {
      await updateCustomFieldDefinition(formTarget.id, data);
    } else {
      await createCustomFieldDefinition(data);
    }
    await load();
  };

  const handleDelete = async (definition: CustomFieldDefinitionItem) => {
    if (!confirm(`Delete custom field "${definition.name}"?`)) return;
    await deleteCustomFieldDefinition(definition.id);
    await load();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Custom Fields</h2>
        <PermissionGuard permission="catalog.custom_fields.manage">
          <button type="button" onClick={() => setFormTarget(null)} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400">
            New custom field
          </button>
        </PermissionGuard>
      </div>

      <div className="flex flex-wrap gap-2">
        {ENTITY_TYPES.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => setEntityType(option.value)}
            className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${
              entityType === option.value
                ? 'bg-cyan-500 text-slate-950'
                : 'bg-slate-200 text-slate-700 hover:bg-slate-300 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>

      {error ? <p className="text-sm text-red-600 dark:text-red-400">{error}</p> : null}

      {loading ? (
        <SkeletonRows count={4} />
      ) : items.length === 0 ? (
        <EmptyState icon={ListPlus} title="No custom fields found" description="Add a custom field to capture extra structured data on this entity type." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Key</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Required</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {items.map((definition) => (
                <tr key={definition.id} className="bg-white dark:bg-slate-900/40">
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{definition.name}</td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{definition.key}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{definition.field_type}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{definition.is_required ? 'Yes' : '—'}</td>
                  <td className="px-4 py-3">
                    <PermissionGuard permission="catalog.custom_fields.manage">
                      <div className="flex justify-end gap-2">
                        <button type="button" onClick={() => setFormTarget(definition)} className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white">
                          <Pencil size={16} />
                        </button>
                        <button type="button" onClick={() => handleDelete(definition)} className="rounded-lg p-1.5 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10">
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </PermissionGuard>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {formTarget !== undefined ? (
        <CustomFieldDefinitionFormModal entityType={entityType} definition={formTarget} onSubmit={handleSave} onClose={() => setFormTarget(undefined)} />
      ) : null}
    </div>
  );
}
