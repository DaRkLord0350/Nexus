'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import { EMPTY_SEO_FIELDS, SeoFieldsSection, seoFieldsFromEntity, seoFieldsToPayload } from '@/components/catalog/seo-fields-section';
import type { CollectionCreateInput } from '@/lib/catalog/collections';
import type { CollectionItem, CollectionRuleCondition, CollectionType } from '@/lib/types';

interface CollectionFormModalProps {
  collection?: CollectionItem | null;
  onSubmit: (data: CollectionCreateInput) => Promise<void>;
  onClose: () => void;
}

export function CollectionFormModal({ collection, onSubmit, onClose }: CollectionFormModalProps) {
  const [name, setName] = useState(collection?.name ?? '');
  const [slug, setSlug] = useState(collection?.slug ?? '');
  const [description, setDescription] = useState(collection?.description ?? '');
  const [imageUrl, setImageUrl] = useState(collection?.image_url ?? '');
  const [collectionType, setCollectionType] = useState(collection?.collection_type ?? 'manual');
  const [status, setStatus] = useState(collection?.status ?? 'active');
  const [isFeatured, setIsFeatured] = useState(collection?.is_featured ?? false);

  const [ruleField, setRuleField] = useState(collection?.rules?.[0]?.field ?? 'is_featured');
  const [ruleValue, setRuleValue] = useState(String(collection?.rules?.[0]?.value ?? 'true'));
  const [seo, setSeo] = useState(collection ? seoFieldsFromEntity(collection) : EMPTY_SEO_FIELDS);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const parsedValue: unknown =
        ruleField === 'is_featured' || ruleField === 'has_variants' ? ruleValue === 'true' : ruleValue;

      await onSubmit({
        name: name.trim(),
        slug: slug.trim() || undefined,
        description: description.trim() || undefined,
        image_url: imageUrl.trim() || undefined,
        collection_type: collectionType,
        rules: collectionType === 'dynamic' ? [{ field: ruleField as never, operator: 'eq', value: parsedValue }] : undefined,
        status,
        is_featured: isFeatured,
        ...seoFieldsToPayload(seo),
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save collection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={collection ? 'Edit collection' : 'New collection'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="max-h-[70vh] space-y-4 overflow-y-auto pr-1">
        <FormError message={error} />

        <div>
          <FormField label="Name" htmlFor="col-name" />
          <FormInput id="col-name" autoFocus value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div>
          <FormField label="Slug (optional)" htmlFor="col-slug" />
          <FormInput id="col-slug" placeholder="auto-generated from name" value={slug} onChange={(e) => setSlug(e.target.value)} />
        </div>
        <div>
          <FormField label="Description" htmlFor="col-description" />
          <FormInput id="col-description" value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>
        <div>
          <FormField label="Image URL" htmlFor="col-image" />
          <FormInput id="col-image" value={imageUrl} onChange={(e) => setImageUrl(e.target.value)} />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Type" htmlFor="col-type" />
            <select
              id="col-type"
              value={collectionType}
              onChange={(e) => setCollectionType(e.target.value as CollectionType)}
              disabled={!!collection}
              className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 disabled:opacity-60 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
            >
              <option value="manual">Manual</option>
              <option value="dynamic">Dynamic</option>
            </select>
          </div>
          <div>
            <FormField label="Status" htmlFor="col-status" />
            <select id="col-status" value={status} onChange={(e) => setStatus(e.target.value as 'draft' | 'active' | 'archived')} className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="archived">Archived</option>
            </select>
          </div>
        </div>

        {collectionType === 'dynamic' ? (
          <div className="space-y-3 rounded-xl border border-slate-200 p-3 dark:border-slate-800">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Dynamic rule</p>
            <div className="grid grid-cols-2 gap-3">
              <select value={ruleField} onChange={(e) => setRuleField(e.target.value as CollectionRuleCondition['field'])} className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
                <option value="is_featured">Featured</option>
                <option value="status">Status</option>
                <option value="category_id">Category ID</option>
                <option value="brand_id">Brand ID</option>
                <option value="tag">Tag</option>
              </select>
              {ruleField === 'is_featured' ? (
                <select value={ruleValue} onChange={(e) => setRuleValue(e.target.value)} className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
                  <option value="true">True</option>
                  <option value="false">False</option>
                </select>
              ) : (
                <FormInput value={ruleValue} onChange={(e) => setRuleValue(e.target.value)} placeholder="value" />
              )}
            </div>
          </div>
        ) : null}

        <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
          <input type="checkbox" checked={isFeatured} onChange={(e) => setIsFeatured(e.target.checked)} />
          Featured
        </label>

        <SeoFieldsSection value={seo} onChange={setSeo} idPrefix="col" />

        <FormButton type="submit" loading={loading}>
          {collection ? 'Save changes' : 'Create collection'}
        </FormButton>
      </form>
    </Modal>
  );
}
