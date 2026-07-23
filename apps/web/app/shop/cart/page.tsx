'use client';

import { ArrowRight, Minus, Plus, ShoppingCart, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError, FormInput } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import {
  addCartItem,
  applyCartCoupon,
  fetchCart,
  getOrCreateMyCart,
  removeCartCoupon,
  removeCartItem,
  updateCartItem,
  type CartDetail,
} from '@/lib/customer-portal/cart';
import { getCustomerOrgId, setCustomerOrgId } from '@/lib/customer-portal/api-client';

export default function ShopCartPage() {
  const [orgId, setOrgId] = useState('');
  const [orgConfirmed, setOrgConfirmed] = useState(false);
  const [cart, setCart] = useState<CartDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newProductId, setNewProductId] = useState('');
  const [newQuantity, setNewQuantity] = useState('1');
  const [couponCode, setCouponCode] = useState('');

  useEffect(() => {
    const stored = getCustomerOrgId();
    if (stored) {
      setOrgId(stored);
      setOrgConfirmed(true);
    } else {
      setLoading(false);
    }
  }, []);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const created = await getOrCreateMyCart();
      const detail = await fetchCart(created.id, created);
      setCart(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load your cart.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (orgConfirmed) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgConfirmed]);

  const handleConfirmOrg = () => {
    if (!orgId.trim()) return;
    setCustomerOrgId(orgId.trim());
    setOrgConfirmed(true);
  };

  const handleAddProduct = async () => {
    if (!cart || !newProductId.trim()) return;
    try {
      await addCartItem(cart.id, cart, newProductId.trim(), Number(newQuantity) || 1);
      setNewProductId('');
      setNewQuantity('1');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to add product.');
    }
  };

  const handleQuantityChange = async (itemId: string, quantity: number) => {
    if (!cart || quantity < 1) return;
    try {
      await updateCartItem(cart.id, cart, itemId, quantity);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update quantity.');
    }
  };

  const handleRemove = async (itemId: string) => {
    if (!cart) return;
    try {
      await removeCartItem(cart.id, cart, itemId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to remove item.');
    }
  };

  const handleApplyCoupon = async () => {
    if (!cart || !couponCode.trim()) return;
    try {
      await applyCartCoupon(cart.id, cart, couponCode.trim());
      setCouponCode('');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to apply coupon.');
    }
  };

  const handleRemoveCoupon = async () => {
    if (!cart) return;
    try {
      await removeCartCoupon(cart.id, cart);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to remove coupon.');
    }
  };

  if (!orgConfirmed) {
    return (
      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Welcome</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">Enter your store&apos;s Organization ID to start shopping.</p>
        <div className="flex gap-2">
          <FormInput placeholder="Organization ID" value={orgId} onChange={(e) => setOrgId(e.target.value)} />
          <button type="button" onClick={handleConfirmOrg} className="rounded-xl bg-cyan-500 px-4 py-2.5 text-sm font-semibold text-slate-950 hover:bg-cyan-400">
            Continue
          </button>
        </div>
      </div>
    );
  }

  if (loading) return <SkeletonRows count={4} />;

  const activeItems = cart?.items.filter((i) => !i.saved_for_later) ?? [];

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Your cart</h2>
      <FormError message={error} />

      <div className="grid grid-cols-[2fr_1fr_auto] gap-2 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
        <FormInput placeholder="Product ID" value={newProductId} onChange={(e) => setNewProductId(e.target.value)} />
        <FormInput type="number" min={1} value={newQuantity} onChange={(e) => setNewQuantity(e.target.value)} />
        <button type="button" onClick={handleAddProduct} className="rounded-xl bg-cyan-500 px-3 text-sm font-semibold text-slate-950 hover:bg-cyan-400">Add</button>
      </div>

      {activeItems.length === 0 ? (
        <EmptyState icon={ShoppingCart} title="Your cart is empty" description="Add a product above to get started." />
      ) : (
        <div className="space-y-3">
          {activeItems.map((item) => (
            <div key={item.id} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
              <div>
                <p className="font-medium text-slate-900 dark:text-white">Product {item.product_id.slice(0, 8)}…</p>
                <p className="text-sm text-slate-500 dark:text-slate-400">{cart?.currency} {item.unit_price.toFixed(2)} each</p>
              </div>
              <div className="flex items-center gap-3">
                <button type="button" onClick={() => handleQuantityChange(item.id, item.quantity - 1)} className="rounded-lg border border-slate-300 p-1 dark:border-slate-700">
                  <Minus size={14} />
                </button>
                <span className="w-6 text-center text-sm">{item.quantity}</span>
                <button type="button" onClick={() => handleQuantityChange(item.id, item.quantity + 1)} className="rounded-lg border border-slate-300 p-1 dark:border-slate-700">
                  <Plus size={14} />
                </button>
                <span className="w-20 text-right text-sm font-medium text-slate-900 dark:text-white">{cart?.currency} {item.line_total.toFixed(2)}</span>
                <button type="button" onClick={() => handleRemove(item.id)} className="rounded-lg p-1.5 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10">
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {cart ? (
        <div className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60">
          {cart.coupon_code ? (
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-700 dark:text-slate-200">Coupon: {cart.coupon_code}</span>
              <button type="button" onClick={handleRemoveCoupon} className="text-red-500 hover:underline">Remove</button>
            </div>
          ) : (
            <div className="flex gap-2">
              <FormInput placeholder="Coupon code" value={couponCode} onChange={(e) => setCouponCode(e.target.value)} />
              <button type="button" onClick={handleApplyCoupon} className="rounded-xl border border-slate-300 px-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200">Apply</button>
            </div>
          )}

          <div className="space-y-1 text-sm">
            <div className="flex justify-between"><span className="text-slate-500 dark:text-slate-400">Subtotal</span><span>{cart.currency} {cart.subtotal.toFixed(2)}</span></div>
            <div className="flex justify-between"><span className="text-slate-500 dark:text-slate-400">Discount</span><span>-{cart.currency} {cart.discount_amount.toFixed(2)}</span></div>
            <div className="flex justify-between font-semibold text-slate-900 dark:text-white"><span>Total</span><span>{cart.currency} {cart.total.toFixed(2)}</span></div>
          </div>

          {activeItems.length > 0 ? (
            <Link href={`/shop/checkout?cartId=${cart.id}`} className="flex items-center justify-center gap-1.5 rounded-xl bg-cyan-500 px-4 py-2.5 text-sm font-semibold text-slate-950 hover:bg-cyan-400">
              Proceed to checkout <ArrowRight size={14} />
            </Link>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
