'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import { EMPTY_SEO_FIELDS, SeoFieldsSection, seoFieldsFromEntity, seoFieldsToPayload } from '@/components/catalog/seo-fields-section';
import type { BrandCreateInput } from '@/lib/catalog/brands';
import type { BrandItem } from '@/lib/types';

interface BrandFormModalProps {
  brand?: BrandItem | null;
  onSubmit: (data: BrandCreateInput) => Promise<void>;
  onClose: () => void;
}

export function BrandFormModal({ brand, onSubmit, onClose }: BrandFormModalProps) {
  const [name, setName] = useState(brand?.name ?? '');
  const [slug, setSlug] = useState(brand?.slug ?? '');
  const [description, setDescription] = useState(brand?.description ?? '');
  const [website, setWebsite] = useState(brand?.website ?? '');
  const [logoUrl, setLogoUrl] = useState(brand?.logo_url ?? '');
  const [status, setStatus] = useState(brand?.status ?? 'active');
  const [isFeatured, setIsFeatured] = useState(brand?.is_featured ?? false);
  const [seo, setSeo] = useState(brand ? seoFieldsFromEntity(brand) : EMPTY_SEO_FIELDS);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
        website: website.trim() || undefined,
        logo_url: logoUrl.trim() || undefined,
        status,
        is_featured: isFeatured,
        ...seoFieldsToPayload(seo),
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save brand.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={brand ? 'Edit brand' : 'New brand'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="max-h-[70vh] space-y-4 overflow-y-auto pr-1">
        <FormError message={error} />

        <div>
          <FormField label="Name" htmlFor="brand-name" />
          <FormInput id="brand-name" autoFocus value={name} onChange={(e) => setName(e.target.value)} required />
        </div>

        <div>
          <FormField label="Slug (optional)" htmlFor="brand-slug" />
          <FormInput id="brand-slug" placeholder="auto-generated from name" value={slug} onChange={(e) => setSlug(e.target.value)} />
        </div>

        <div>
          <FormField label="Description" htmlFor="brand-description" />
          <FormInput id="brand-description" value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>

        <div>
          <FormField label="Website" htmlFor="brand-website" />
          <FormInput id="brand-website" value={website} onChange={(e) => setWebsite(e.target.value)} />
        </div>

        <div>
          <FormField label="Logo URL" htmlFor="brand-logo" />
          <FormInput id="brand-logo" value={logoUrl} onChange={(e) => setLogoUrl(e.target.value)} />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Status" htmlFor="brand-status" />
            <select
              id="brand-status"
              value={status}
              onChange={(e) => setStatus(e.target.value as 'draft' | 'active' | 'archived')}
              className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
            >
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="archived">Archived</option>
            </select>
          </div>
          <label className="mt-6 flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input type="checkbox" checked={isFeatured} onChange={(e) => setIsFeatured(e.target.checked)} />
            Featured
          </label>
        </div>

        <SeoFieldsSection value={seo} onChange={setSeo} idPrefix="brand" />

        <FormButton type="submit" loading={loading}>
          {brand ? 'Save changes' : 'Create brand'}
        </FormButton>
      </form>
    </Modal>
  );
}
