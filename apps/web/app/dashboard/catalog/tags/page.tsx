'use client';

import { Pencil, Tag as TagIcon, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { TagFormModal } from '@/components/catalog/tag-form-modal';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError, FormInput } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { createTag, deleteTag, fetchTags, updateTag, type TagCreateInput } from '@/lib/catalog/tags';
import type { TagItem } from '@/lib/types';

export default function TagsPage() {
  const [items, setItems] = useState<TagItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState('');
  const [formTarget, setFormTarget] = useState<TagItem | null | undefined>(undefined);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchTags(q || undefined);
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load tags.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSave = async (data: TagCreateInput) => {
    if (formTarget) {
      await updateTag(formTarget.id, data);
    } else {
      await createTag(data);
    }
    await load();
  };

  const handleDelete = async (tag: TagItem) => {
    if (!confirm(`Delete tag "${tag.name}"?`)) return;
    await deleteTag(tag.id);
    await load();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Tags</h2>
        <PermissionGuard permission="catalog.tags.manage">
          <button type="button" onClick={() => setFormTarget(null)} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400">
            New tag
          </button>
        </PermissionGuard>
      </div>

      <div className="flex gap-3">
        <FormInput
          placeholder="Search tags…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') load(); }}
        />
        <button type="button" onClick={load} className="shrink-0 rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400">
          Search
        </button>
      </div>

      <FormError message={error} />

      {loading ? (
        <SkeletonRows count={5} />
      ) : items.length === 0 ? (
        <EmptyState icon={TagIcon} title="No tags found" description="Tags are created automatically when you tag a product, or you can create one here." />
      ) : (
        <div className="flex flex-wrap gap-2">
          {items.map((tag) => (
            <div key={tag.id} className="flex items-center gap-2 rounded-full border border-slate-300 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900/60">
              <span className="text-slate-700 dark:text-slate-200">{tag.name}</span>
              <PermissionGuard permission="catalog.tags.manage">
                <button type="button" onClick={() => setFormTarget(tag)} className="text-slate-400 hover:text-slate-900 dark:hover:text-white">
                  <Pencil size={12} />
                </button>
                <button type="button" onClick={() => handleDelete(tag)} className="text-red-400 hover:text-red-600">
                  <Trash2 size={12} />
                </button>
              </PermissionGuard>
            </div>
          ))}
        </div>
      )}

      {formTarget !== undefined ? (
        <TagFormModal tag={formTarget} onSubmit={handleSave} onClose={() => setFormTarget(undefined)} />
      ) : null}
    </div>
  );
}
