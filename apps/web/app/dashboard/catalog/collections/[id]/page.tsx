'use client';

import { ArrowLeft, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError, FormInput } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { addCollectionProducts, fetchCollectionProducts, fetchCollections, removeCollectionProducts } from '@/lib/catalog/collections';
import { fetchProducts } from '@/lib/catalog/products';
import type { CollectionItem, ProductItem } from '@/lib/types';

export default function CollectionDetailPage() {
  const params = useParams<{ id: string }>();
  const collectionId = params.id;

  const [collection, setCollection] = useState<CollectionItem | null>(null);
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<ProductItem[]>([]);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [collectionsData, productsData] = await Promise.all([
        fetchCollections({ limit: 200 }),
        fetchCollectionProducts(collectionId),
      ]);
      setCollection(collectionsData.items.find((c) => c.id === collectionId) ?? null);
      setProducts(productsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load collection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (collectionId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [collectionId]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    const data = await fetchProducts({ q: searchQuery, limit: 10 });
    setSearchResults(data.items.filter((p) => !products.some((existing) => existing.id === p.id)));
  };

  const handleAdd = async (product: ProductItem) => {
    await addCollectionProducts(collectionId, [product.id]);
    setSearchResults((prev) => prev.filter((p) => p.id !== product.id));
    await load();
  };

  const handleRemove = async (product: ProductItem) => {
    await removeCollectionProducts(collectionId, [product.id]);
    await load();
  };

  if (loading) return <SkeletonRows count={6} />;

  return (
    <div className="space-y-6">
      <Link href="/dashboard/catalog/collections" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
        <ArrowLeft size={14} /> Back to collections
      </Link>

      <FormError message={error} />

      {!collection ? (
        <EmptyState title="Collection not found" />
      ) : (
        <>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{collection.name}</h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {collection.collection_type === 'manual' ? 'Manual collection' : 'Dynamic collection (products resolved automatically by rule)'} · {collection.status}
            </p>
          </div>

          {collection.collection_type === 'manual' ? (
            <PermissionGuard permission="catalog.collections.manage">
              <div className="rounded-2xl border border-slate-200 p-4 dark:border-slate-800">
                <p className="mb-2 text-sm font-medium text-slate-700 dark:text-slate-300">Add products</p>
                <div className="flex gap-2">
                  <FormInput placeholder="Search products by name or SKU…" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') handleSearch(); }} />
                  <button type="button" onClick={handleSearch} className="shrink-0 rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400">Search</button>
                </div>
                {searchResults.length > 0 ? (
                  <div className="mt-3 space-y-1.5">
                    {searchResults.map((product) => (
                      <div key={product.id} className="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-950/60">
                        <span>{product.name} <span className="text-slate-400">({product.sku})</span></span>
                        <button type="button" onClick={() => handleAdd(product)} className="text-xs font-semibold text-cyan-600 dark:text-cyan-400">Add</button>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            </PermissionGuard>
          ) : null}

          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Products ({products.length})</h3>
          {products.length === 0 ? (
            <EmptyState title="No products in this collection yet" />
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                  <tr>
                    <th className="px-4 py-3">Name</th>
                    <th className="px-4 py-3">SKU</th>
                    <th className="px-4 py-3">Status</th>
                    {collection.collection_type === 'manual' ? <th className="px-4 py-3 text-right">Actions</th> : null}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {products.map((product) => (
                    <tr key={product.id} className="bg-white dark:bg-slate-900/40">
                      <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{product.name}</td>
                      <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{product.sku}</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{product.status}</td>
                      {collection.collection_type === 'manual' ? (
                        <td className="px-4 py-3 text-right">
                          <PermissionGuard permission="catalog.collections.manage">
                            <button type="button" onClick={() => handleRemove(product)} className="rounded-lg p-1.5 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10">
                              <Trash2 size={16} />
                            </button>
                          </PermissionGuard>
                        </td>
                      ) : null}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
