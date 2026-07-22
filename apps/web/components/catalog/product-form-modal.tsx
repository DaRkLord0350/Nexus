'use client';

import { useEffect, useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import { EMPTY_SEO_FIELDS, SeoFieldsSection, seoFieldsFromEntity, seoFieldsToPayload } from '@/components/catalog/seo-fields-section';
import { fetchBrands } from '@/lib/catalog/brands';
import { fetchCategories } from '@/lib/catalog/categories';
import { fetchProductTypes } from '@/lib/catalog/product-types';
import type { ProductCreateInput } from '@/lib/catalog/products';
import { fetchTaxClasses } from '@/lib/catalog/tax';
import type { BrandItem, CategoryItem, ProductItem, ProductTypeItem, TaxClassItem } from '@/lib/types';

interface ProductFormModalProps {
  product?: ProductItem | null;
  onSubmit: (data: ProductCreateInput) => Promise<void>;
  onClose: () => void;
}

export function ProductFormModal({ product, onSubmit, onClose }: ProductFormModalProps) {
  const [name, setName] = useState(product?.name ?? '');
  const [slug, setSlug] = useState(product?.slug ?? '');
  const [sku, setSku] = useState(product?.sku ?? '');
  const [barcode, setBarcode] = useState(product?.barcode ?? '');
  const [brandId, setBrandId] = useState(product?.brand_id ?? '');
  const [categoryId, setCategoryId] = useState(product?.category_id ?? '');
  const [taxClassId, setTaxClassId] = useState(product?.tax_class_id ?? '');
  const [productTypeId, setProductTypeId] = useState(product?.product_type_id ?? '');
  const [shortDescription, setShortDescription] = useState(product?.short_description ?? '');
  const [description, setDescription] = useState(product?.description ?? '');
  const [status, setStatus] = useState(product?.status ?? 'draft');
  const [vendor, setVendor] = useState(product?.vendor ?? '');
  const [tags, setTags] = useState((product?.tags ?? []).map((t) => t.name).join(', '));
  const [weight, setWeight] = useState(product?.weight ?? undefined);
  const [trackInventory, setTrackInventory] = useState(product?.track_inventory ?? true);
  const [allowBackorders, setAllowBackorders] = useState(product?.allow_backorders ?? false);
  const [hasVariants, setHasVariants] = useState(product?.has_variants ?? false);
  const [isFeatured, setIsFeatured] = useState(product?.is_featured ?? false);
  const [seo, setSeo] = useState(product ? seoFieldsFromEntity(product) : EMPTY_SEO_FIELDS);

  const [brands, setBrands] = useState<BrandItem[]>([]);
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  const [taxClasses, setTaxClasses] = useState<TaxClassItem[]>([]);
  const [productTypes, setProductTypes] = useState<ProductTypeItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBrands({ limit: 200 }).then((data) => setBrands(data.items)).catch(() => setBrands([]));
    fetchCategories({ limit: 200 }).then((data) => setCategories(data.items)).catch(() => setCategories([]));
    fetchTaxClasses().then((data) => setTaxClasses(data.items)).catch(() => setTaxClasses([]));
    fetchProductTypes().then((data) => setProductTypes(data.items)).catch(() => setProductTypes([]));
  }, []);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim() || !sku.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        name: name.trim(),
        slug: slug.trim() || undefined,
        sku: sku.trim(),
        barcode: barcode.trim() || undefined,
        brand_id: brandId || null,
        category_id: categoryId || null,
        tax_class_id: taxClassId || null,
        product_type_id: productTypeId || null,
        short_description: shortDescription.trim() || undefined,
        description: description.trim() || undefined,
        status,
        vendor: vendor.trim() || undefined,
        tag_names: tags.trim() ? tags.split(',').map((t) => t.trim()).filter(Boolean) : [],
        weight,
        track_inventory: trackInventory,
        allow_backorders: allowBackorders,
        has_variants: hasVariants,
        is_featured: isFeatured,
        ...seoFieldsToPayload(seo),
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save product.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={product ? 'Edit product' : 'New product'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="max-h-[70vh] space-y-4 overflow-y-auto pr-1">
        <FormError message={error} />

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Name" htmlFor="prod-name" />
            <FormInput id="prod-name" autoFocus value={name} onChange={(e) => setName(e.target.value)} required />
          </div>
          <div>
            <FormField label="SKU" htmlFor="prod-sku" />
            <FormInput id="prod-sku" value={sku} onChange={(e) => setSku(e.target.value)} required />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Slug (optional)" htmlFor="prod-slug" />
            <FormInput id="prod-slug" placeholder="auto-generated" value={slug} onChange={(e) => setSlug(e.target.value)} />
          </div>
          <div>
            <FormField label="Barcode" htmlFor="prod-barcode" />
            <FormInput id="prod-barcode" value={barcode} onChange={(e) => setBarcode(e.target.value)} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Brand" htmlFor="prod-brand" />
            <select id="prod-brand" value={brandId ?? ''} onChange={(e) => setBrandId(e.target.value)} className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
              <option value="">No brand</option>
              {brands.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
          </div>
          <div>
            <FormField label="Category" htmlFor="prod-category" />
            <select id="prod-category" value={categoryId ?? ''} onChange={(e) => setCategoryId(e.target.value)} className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
              <option value="">No category</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.path}</option>)}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Tax class" htmlFor="prod-tax-class" />
            <select id="prod-tax-class" value={taxClassId ?? ''} onChange={(e) => setTaxClassId(e.target.value)} className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
              <option value="">No tax class</option>
              {taxClasses.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>
          <div>
            <FormField label="Product type" htmlFor="prod-type" />
            <select id="prod-type" value={productTypeId ?? ''} onChange={(e) => setProductTypeId(e.target.value)} className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
              <option value="">No product type</option>
              {productTypes.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>
        </div>

        <div>
          <FormField label="Short description" htmlFor="prod-short-desc" />
          <FormInput id="prod-short-desc" value={shortDescription} onChange={(e) => setShortDescription(e.target.value)} />
        </div>
        <div>
          <FormField label="Description" htmlFor="prod-desc" />
          <FormInput id="prod-desc" value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <FormField label="Status" htmlFor="prod-status" />
            <select id="prod-status" value={status} onChange={(e) => setStatus(e.target.value as 'draft' | 'published' | 'archived')} className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
              <option value="draft">Draft</option>
              <option value="published">Published</option>
              <option value="archived">Archived</option>
            </select>
          </div>
          <div>
            <FormField label="Vendor" htmlFor="prod-vendor" />
            <FormInput id="prod-vendor" value={vendor} onChange={(e) => setVendor(e.target.value)} />
          </div>
          <div>
            <FormField label="Weight" htmlFor="prod-weight" />
            <FormInput id="prod-weight" type="number" value={weight ?? ''} onChange={(e) => setWeight(e.target.value ? Number(e.target.value) : undefined)} />
          </div>
        </div>

        <div>
          <FormField label="Tags (comma-separated)" htmlFor="prod-tags" />
          <FormInput id="prod-tags" value={tags} onChange={(e) => setTags(e.target.value)} placeholder="new, bestseller" />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input type="checkbox" checked={trackInventory} onChange={(e) => setTrackInventory(e.target.checked)} />
            Track inventory
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input type="checkbox" checked={allowBackorders} onChange={(e) => setAllowBackorders(e.target.checked)} />
            Allow backorders
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input type="checkbox" checked={hasVariants} onChange={(e) => setHasVariants(e.target.checked)} />
            Has variants
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input type="checkbox" checked={isFeatured} onChange={(e) => setIsFeatured(e.target.checked)} />
            Featured
          </label>
        </div>

        <SeoFieldsSection value={seo} onChange={setSeo} idPrefix="prod" />

        <FormButton type="submit" loading={loading}>
          {product ? 'Save changes' : 'Create product'}
        </FormButton>
      </form>
    </Modal>
  );
}
