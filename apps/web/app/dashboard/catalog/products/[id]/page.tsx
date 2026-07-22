'use client';

import { ArrowLeft, Pencil, Star, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ChannelToggles } from '@/components/catalog/channel-toggles';
import { CustomFieldsPanel } from '@/components/catalog/custom-fields-panel';
import { MediaGallery } from '@/components/catalog/media-gallery';
import { PricingTable } from '@/components/catalog/pricing-table';
import { ProductFormModal } from '@/components/catalog/product-form-modal';
import { VariantFormModal } from '@/components/catalog/variant-form-modal';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { fetchProductChannels } from '@/lib/catalog/channels';
import { fetchMediaForProduct } from '@/lib/catalog/media';
import { fetchPrices } from '@/lib/catalog/pricing';
import { fetchProduct, updateProduct, type ProductCreateInput } from '@/lib/catalog/products';
import {
  createVariant,
  deleteVariant,
  fetchVariants,
  setDefaultVariant,
  updateVariant,
  type VariantCreateInput,
} from '@/lib/catalog/variants';
import type { MediaItem, ProductChannelItem, ProductItem, ProductPriceItem, VariantItem } from '@/lib/types';

export default function ProductDetailPage() {
  const params = useParams<{ id: string }>();
  const productId = params.id;

  const [product, setProduct] = useState<ProductItem | null>(null);
  const [variants, setVariants] = useState<VariantItem[]>([]);
  const [media, setMedia] = useState<MediaItem[]>([]);
  const [prices, setPrices] = useState<ProductPriceItem[]>([]);
  const [channels, setChannels] = useState<ProductChannelItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editingProduct, setEditingProduct] = useState(false);
  const [variantFormTarget, setVariantFormTarget] = useState<VariantItem | null | undefined>(undefined);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [productData, variantData, mediaData, priceData, channelData] = await Promise.all([
        fetchProduct(productId),
        fetchVariants(productId),
        fetchMediaForProduct(productId),
        fetchPrices(productId),
        fetchProductChannels(productId),
      ]);
      setProduct(productData);
      setVariants(variantData.items);
      setMedia(mediaData.items);
      setPrices(priceData.items);
      setChannels(channelData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load product.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (productId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productId]);

  const handleSaveProduct = async (data: ProductCreateInput) => {
    await updateProduct(productId, data);
    await load();
  };

  const handleSaveVariant = async (data: VariantCreateInput) => {
    if (variantFormTarget) {
      await updateVariant(productId, variantFormTarget.id, data);
    } else {
      await createVariant(productId, data);
    }
    await load();
  };

  const handleDeleteVariant = async (variant: VariantItem) => {
    if (!confirm(`Delete variant "${variant.sku}"?`)) return;
    await deleteVariant(productId, variant.id);
    await load();
  };

  const handleSetDefault = async (variant: VariantItem) => {
    await setDefaultVariant(productId, variant.id);
    await load();
  };

  if (loading) return <SkeletonRows count={6} />;

  return (
    <div className="space-y-6">
      <Link href="/dashboard/catalog/products" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
        <ArrowLeft size={14} /> Back to products
      </Link>

      <FormError message={error} />

      {!product ? (
        <EmptyState title="Product not found" />
      ) : (
        <>
          <div className="flex items-start justify-between rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{product.name}</h2>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">SKU {product.sku} · {product.status}</p>
              {product.short_description ? <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">{product.short_description}</p> : null}
            </div>
            <PermissionGuard permission="catalog.products.edit">
              <button type="button" onClick={() => setEditingProduct(true)} className="flex items-center gap-1.5 rounded-xl border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 dark:border-slate-700 dark:text-slate-200">
                <Pencil size={14} /> Edit
              </button>
            </PermissionGuard>
          </div>

          <ChannelToggles productId={productId} assigned={channels} onChange={load} />

          <CustomFieldsPanel entityType="product" entityId={productId} />

          <MediaGallery productId={productId} items={media} onChange={load} />

          <PricingTable productId={productId} items={prices} onChange={load} />

          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Variants</h3>
            <PermissionGuard permission="catalog.variants.manage">
              <button type="button" onClick={() => setVariantFormTarget(null)} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400">
                New variant
              </button>
            </PermissionGuard>
          </div>

          {variants.length === 0 ? (
            <EmptyState title="No variants yet" description="Add a variant to sell this product in multiple options (size, color, etc.)." />
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                  <tr>
                    <th className="px-4 py-3">SKU</th>
                    <th className="px-4 py-3">Attributes</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Default</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {variants.map((variant) => (
                    <tr key={variant.id} className="bg-white dark:bg-slate-900/40">
                      <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{variant.sku}</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                        {variant.attribute_values.map((v) => v.value).join(', ') || '—'}
                      </td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{variant.status}</td>
                      <td className="px-4 py-3">
                        {variant.is_default ? (
                          <Star size={16} className="fill-amber-400 text-amber-400" />
                        ) : (
                          <PermissionGuard permission="catalog.variants.manage">
                            <button type="button" onClick={() => handleSetDefault(variant)} className="text-xs text-slate-400 hover:text-slate-700 dark:hover:text-slate-200">
                              Set default
                            </button>
                          </PermissionGuard>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <PermissionGuard permission="catalog.variants.manage">
                          <div className="flex justify-end gap-2">
                            <button type="button" onClick={() => setVariantFormTarget(variant)} className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white">
                              <Pencil size={16} />
                            </button>
                            <button type="button" onClick={() => handleDeleteVariant(variant)} className="rounded-lg p-1.5 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10">
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
        </>
      )}

      {editingProduct && product ? (
        <ProductFormModal product={product} onSubmit={handleSaveProduct} onClose={() => setEditingProduct(false)} />
      ) : null}
      {variantFormTarget !== undefined ? (
        <VariantFormModal variant={variantFormTarget} onSubmit={handleSaveVariant} onClose={() => setVariantFormTarget(undefined)} />
      ) : null}
    </div>
  );
}
