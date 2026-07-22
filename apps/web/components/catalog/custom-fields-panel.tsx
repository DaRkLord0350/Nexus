'use client';

import { useEffect, useState } from 'react';
import { PermissionGuard } from '@/components/permission-guard';
import { FormButton, FormField, FormInput } from '@/components/ui/form';
import { fetchCustomFieldValues, setCustomFieldValues } from '@/lib/catalog/custom-fields';
import type { CustomFieldEntityType, CustomFieldValueItem } from '@/lib/types';

interface CustomFieldsPanelProps {
  entityType: CustomFieldEntityType;
  entityId: string;
}

export function CustomFieldsPanel({ entityType, entityId }: CustomFieldsPanelProps) {
  const [fields, setFields] = useState<CustomFieldValueItem[]>([]);
  const [draft, setDraft] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const values = await fetchCustomFieldValues(entityType, entityId);
      setFields(values);
      setDraft(Object.fromEntries(values.map((v) => [v.key, v.value ?? ''])));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entityId]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await setCustomFieldValues(entityType, entityId, draft);
      await load();
    } finally {
      setSaving(false);
    }
  };

  if (loading || fields.length === 0) return null;

  return (
    <div className="space-y-3">
      <h3 className="font-semibold text-slate-900 dark:text-white">Custom Fields</h3>
      <div className="grid gap-3 sm:grid-cols-2">
        {fields.map((field) => (
          <div key={field.definition_id}>
            <FormField label={field.name} htmlFor={`cf-${field.definition_id}`} />
            {field.field_type === 'boolean' ? (
              <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                <input
                  type="checkbox"
                  checked={Boolean(draft[field.key])}
                  onChange={(e) => setDraft((prev) => ({ ...prev, [field.key]: e.target.checked }))}
                />
                {field.key}
              </label>
            ) : (
              <FormInput
                id={`cf-${field.definition_id}`}
                type={field.field_type === 'number' ? 'number' : field.field_type === 'date' ? 'date' : 'text'}
                value={(draft[field.key] as string | number) ?? ''}
                onChange={(e) =>
                  setDraft((prev) => ({
                    ...prev,
                    [field.key]: field.field_type === 'number' ? Number(e.target.value) : e.target.value,
                  }))
                }
              />
            )}
          </div>
        ))}
      </div>
      <PermissionGuard permission="catalog.custom_fields.manage">
        <FormButton type="button" onClick={handleSave} loading={saving} className="w-auto px-4">
          Save custom fields
        </FormButton>
      </PermissionGuard>
    </div>
  );
}
