'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import { EMPTY_SEO_FIELDS, SeoFieldsSection, seoFieldsFromEntity, seoFieldsToPayload } from '@/components/catalog/seo-fields-section';
import type { CategoryCreateInput } from '@/lib/catalog/categories';
import type { CategoryItem } from '@/lib/types';

interface CategoryFormModalProps {
  category?: CategoryItem | null;
  categories: CategoryItem[];
  onSubmit: (data: CategoryCreateInput) => Promise<void>;
  onClose: () => void;
}

export function CategoryFormModal({ category, categories, onSubmit, onClose }: CategoryFormModalProps) {
  const [name, setName] = useState(category?.name ?? '');
  const [slug, setSlug] = useState(category?.slug ?? '');
  const [description, setDescription] = useState(category?.description ?? '');
  const [parentId, setParentId] = useState(category?.parent_id ?? '');
  const [status, setStatus] = useState(category?.status ?? 'active');
  const [isFeatured, setIsFeatured] = useState(category?.is_featured ?? false);
  const [isVisible, setIsVisible] = useState(category?.is_visible ?? true);
  const [sortOrder, setSortOrder] = useState(category?.sort_order ?? 0);
  const [imageUrl, setImageUrl] = useState(category?.image_url ?? '');
  const [seo, setSeo] = useState(category ? seoFieldsFromEntity(category) : EMPTY_SEO_FIELDS);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const parentOptions = categories.filter((c) => c.id !== category?.id);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        name: name.trim(),
        slug: slug.trim() || undefined,
        description: description.trim() || undefined,
        parent_id: parentId || null,
        status,
        is_featured: isFeatured,
        is_visible: isVisible,
        sort_order: sortOrder,
        image_url: imageUrl.trim() || undefined,
        ...seoFieldsToPayload(seo),
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save category.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={category ? 'Edit category' : 'New category'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="max-h-[70vh] space-y-4 overflow-y-auto pr-1">
        <FormError message={error} />

        <div>
          <FormField label="Name" htmlFor="cat-name" />
          <FormInput id="cat-name" autoFocus value={name} onChange={(e) => setName(e.target.value)} required />
        </div>

        <div>
          <FormField label="Slug (optional)" htmlFor="cat-slug" />
          <FormInput id="cat-slug" placeholder="auto-generated from name" value={slug} onChange={(e) => setSlug(e.target.value)} />
        </div>

        <div>
          <FormField label="Description" htmlFor="cat-description" />
          <FormInput id="cat-description" value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>

        <div>
          <FormField label="Parent category" htmlFor="cat-parent" />
          <select
            id="cat-parent"
            value={parentId ?? ''}
            onChange={(e) => setParentId(e.target.value)}
            className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
          >
            <option value="">No parent (top-level)</option>
            {parentOptions.map((option) => (
              <option key={option.id} value={option.id}>{option.path}</option>
            ))}
          </select>
        </div>

        <div>
          <FormField label="Image URL" htmlFor="cat-image" />
          <FormInput id="cat-image" value={imageUrl} onChange={(e) => setImageUrl(e.target.value)} />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Status" htmlFor="cat-status" />
            <select
              id="cat-status"
              value={status}
              onChange={(e) => setStatus(e.target.value as 'draft' | 'active' | 'archived')}
              className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
            >
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="archived">Archived</option>
            </select>
          </div>
          <div>
            <FormField label="Sort order" htmlFor="cat-sort" />
            <FormInput
              id="cat-sort"
              type="number"
              value={sortOrder}
              onChange={(e) => setSortOrder(Number(e.target.value) || 0)}
            />
          </div>
        </div>

        <div className="flex gap-6">
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input type="checkbox" checked={isFeatured} onChange={(e) => setIsFeatured(e.target.checked)} />
            Featured
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input type="checkbox" checked={isVisible} onChange={(e) => setIsVisible(e.target.checked)} />
            Visible
          </label>
        </div>

        <SeoFieldsSection value={seo} onChange={setSeo} idPrefix="cat" />

        <FormButton type="submit" loading={loading}>
          {category ? 'Save changes' : 'Create category'}
        </FormButton>
      </form>
    </Modal>
  );
}
