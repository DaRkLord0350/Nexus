'use client';

import { FolderTree, Pencil, Plus, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { CategoryFormModal } from '@/components/catalog/category-form-modal';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError, FormInput } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import {
  createCategory,
  deleteCategory,
  fetchCategories,
  updateCategory,
  type CategoryCreateInput,
} from '@/lib/catalog/categories';
import type { CategoryItem } from '@/lib/types';

const PAGE_SIZE = 25;

export default function CategoriesPage() {
  const [items, setItems] = useState<CategoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const [formTarget, setFormTarget] = useState<CategoryItem | null | undefined>(undefined);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCategories({
        q: q || undefined,
        status: statusFilter || undefined,
        sortBy: 'sort_order',
        sortOrder: 'asc',
        limit: PAGE_SIZE,
        offset,
      });
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load categories.');
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

  const handleSave = async (data: CategoryCreateInput) => {
    if (formTarget) {
      await updateCategory(formTarget.id, data);
    } else {
      await createCategory(data);
    }
    await load();
  };

  const handleDelete = async (category: CategoryItem) => {
    if (!confirm(`Delete "${category.name}"? Subcategories will need cascade delete if present.`)) return;
    try {
      await deleteCategory(category.id);
      await load();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to delete category.';
      if (message.toLowerCase().includes('subcategories') && confirm(`${message}\n\nDelete it and all subcategories?`)) {
        await deleteCategory(category.id, true);
        await load();
      } else {
        setError(message);
      }
    }
  };

  const depth = (path: string) => path.split('/').length - 1;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Categories</h2>
        <PermissionGuard permission="catalog.categories.manage">
          <button
            type="button"
            onClick={() => setFormTarget(null)}
            className="flex items-center gap-2 rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400"
          >
            <Plus size={16} />
            New category
          </button>
        </PermissionGuard>
      </div>

      <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60 sm:grid-cols-3">
        <FormInput placeholder="Search by name or slug…" value={q} onChange={(e) => setQ(e.target.value)} />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
        >
          <option value="">All statuses</option>
          <option value="draft">Draft</option>
          <option value="active">Active</option>
          <option value="archived">Archived</option>
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

      {loading ? (
        <SkeletonRows count={6} />
      ) : items.length === 0 ? (
        <EmptyState icon={FolderTree} title="No categories found" description="Create your first category to start building the catalog tree." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Slug</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Featured</th>
                <th className="px-4 py-3">Visible</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {items.map((item) => (
                <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-white" style={{ paddingLeft: `${16 + depth(item.path) * 20}px` }}>
                    {item.name}
                  </td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{item.slug}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.status}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.is_featured ? 'Yes' : '—'}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.is_visible ? 'Yes' : 'Hidden'}</td>
                  <td className="px-4 py-3">
                    <PermissionGuard permission="catalog.categories.manage">
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => setFormTarget(item)}
                          className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
                        >
                          <Pencil size={16} />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(item)}
                          className="rounded-lg p-1.5 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10"
                        >
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

      {total > 0 ? (
        <div className="flex items-center justify-between text-sm text-slate-500 dark:text-slate-400">
          <span>Page {currentPage} of {totalPages} ({total} total)</span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
              className="rounded-lg border border-slate-300 px-3 py-1.5 font-medium text-slate-700 disabled:opacity-40 dark:border-slate-700 dark:text-slate-200"
            >
              Previous
            </button>
            <button
              type="button"
              disabled={offset + PAGE_SIZE >= total}
              onClick={() => setOffset(offset + PAGE_SIZE)}
              className="rounded-lg border border-slate-300 px-3 py-1.5 font-medium text-slate-700 disabled:opacity-40 dark:border-slate-700 dark:text-slate-200"
            >
              Next
            </button>
          </div>
        </div>
      ) : null}

      {formTarget !== undefined ? (
        <CategoryFormModal
          category={formTarget}
          categories={items}
          onSubmit={handleSave}
          onClose={() => setFormTarget(undefined)}
        />
      ) : null}
    </div>
  );
}
