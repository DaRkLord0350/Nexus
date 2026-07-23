'use client';

import { Heart, ShoppingCart, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { fetchMyWishlist, moveMyWishlistItemToCart, removeMyWishlistItem, type WishlistItem } from '@/lib/customer-portal/wishlist';

export default function PortalWishlistPage() {
  const [items, setItems] = useState<WishlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchMyWishlist();
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load your wishlist.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleRemove = async (itemId: string) => {
    try {
      await removeMyWishlistItem(itemId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to remove item.');
    }
  };

  const handleMoveToCart = async (itemId: string) => {
    try {
      await moveMyWishlistItemToCart(itemId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to move item to cart.');
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-slate-900 dark:text-white">My wishlist</h2>
      <FormError message={error} />
      {loading ? (
        <SkeletonRows count={4} />
      ) : items.length === 0 ? (
        <EmptyState icon={Heart} title="Your wishlist is empty" description="Save products you love to find them here later." />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {items.map((item) => (
            <div key={item.id} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-4 text-sm dark:border-slate-800 dark:bg-slate-900/60">
              <div>
                <p className="font-medium text-slate-900 dark:text-white">Product {item.product_id.slice(0, 8)}…</p>
                {item.notes ? <p className="text-slate-500 dark:text-slate-400">{item.notes}</p> : null}
              </div>
              <div className="flex gap-2">
                <button type="button" onClick={() => handleMoveToCart(item.id)} className="rounded-lg p-1.5 text-cyan-600 hover:bg-cyan-50 dark:text-cyan-400 dark:hover:bg-cyan-500/10" title="Move to cart">
                  <ShoppingCart size={16} />
                </button>
                <button type="button" onClick={() => handleRemove(item.id)} className="rounded-lg p-1.5 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10" title="Remove">
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
