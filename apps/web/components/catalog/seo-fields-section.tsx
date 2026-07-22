'use client';

import { useState } from 'react';
import { FormField, FormInput } from '@/components/ui/form';

export interface SeoFieldsValue {
  seo_title: string;
  seo_description: string;
  seo_keywords: string;
  og_image_url: string;
  canonical_url: string;
  no_index: boolean;
}

export const EMPTY_SEO_FIELDS: SeoFieldsValue = {
  seo_title: '',
  seo_description: '',
  seo_keywords: '',
  og_image_url: '',
  canonical_url: '',
  no_index: false,
};

interface SeoFieldsSectionProps {
  value: SeoFieldsValue;
  onChange: (value: SeoFieldsValue) => void;
  idPrefix: string;
}

export function SeoFieldsSection({ value, onChange, idPrefix }: SeoFieldsSectionProps) {
  const [open, setOpen] = useState(false);
  const set = (patch: Partial<SeoFieldsValue>) => onChange({ ...value, ...patch });

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-800">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex w-full items-center justify-between px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-200"
      >
        SEO
        <span className="text-xs text-slate-400">{open ? 'Hide' : 'Show'}</span>
      </button>
      {open ? (
        <div className="space-y-3 border-t border-slate-100 p-3 dark:border-slate-800">
          <div>
            <FormField label="SEO title" htmlFor={`${idPrefix}-seo-title`} />
            <FormInput id={`${idPrefix}-seo-title`} value={value.seo_title} onChange={(e) => set({ seo_title: e.target.value })} />
          </div>
          <div>
            <FormField label="SEO description" htmlFor={`${idPrefix}-seo-description`} />
            <FormInput id={`${idPrefix}-seo-description`} value={value.seo_description} onChange={(e) => set({ seo_description: e.target.value })} />
          </div>
          <div>
            <FormField label="SEO keywords" htmlFor={`${idPrefix}-seo-keywords`} />
            <FormInput id={`${idPrefix}-seo-keywords`} value={value.seo_keywords} onChange={(e) => set({ seo_keywords: e.target.value })} placeholder="comma-separated" />
          </div>
          <div>
            <FormField label="Social share image (og:image)" htmlFor={`${idPrefix}-og-image`} />
            <FormInput id={`${idPrefix}-og-image`} value={value.og_image_url} onChange={(e) => set({ og_image_url: e.target.value })} />
          </div>
          <div>
            <FormField label="Canonical URL" htmlFor={`${idPrefix}-canonical`} />
            <FormInput id={`${idPrefix}-canonical`} value={value.canonical_url} onChange={(e) => set({ canonical_url: e.target.value })} />
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input type="checkbox" checked={value.no_index} onChange={(e) => set({ no_index: e.target.checked })} />
            Hide from search engines (noindex)
          </label>
        </div>
      ) : null}
    </div>
  );
}

interface SeoFieldsSource {
  seo_title?: string | null;
  seo_description?: string | null;
  seo_keywords?: string | null;
  og_image_url?: string | null;
  canonical_url?: string | null;
  no_index?: boolean | null;
}

export function seoFieldsFromEntity(entity?: SeoFieldsSource | null): SeoFieldsValue {
  return {
    seo_title: entity?.seo_title ?? '',
    seo_description: entity?.seo_description ?? '',
    seo_keywords: entity?.seo_keywords ?? '',
    og_image_url: entity?.og_image_url ?? '',
    canonical_url: entity?.canonical_url ?? '',
    no_index: entity?.no_index ?? false,
  };
}

export function seoFieldsToPayload(value: SeoFieldsValue) {
  return {
    seo_title: value.seo_title.trim() || undefined,
    seo_description: value.seo_description.trim() || undefined,
    seo_keywords: value.seo_keywords.trim() || undefined,
    og_image_url: value.og_image_url.trim() || undefined,
    canonical_url: value.canonical_url.trim() || undefined,
    no_index: value.no_index,
  };
}
