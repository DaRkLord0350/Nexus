'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { CouponCreateInput } from '@/lib/catalog/coupons';
import type { CouponDiscountType, CouponItem } from '@/lib/types';

interface CouponFormModalProps {
  coupon?: CouponItem | null;
  onSubmit: (data: CouponCreateInput) => Promise<void>;
  onClose: () => void;
}

export function CouponFormModal({ coupon, onSubmit, onClose }: CouponFormModalProps) {
  const [code, setCode] = useState(coupon?.code ?? '');
  const [name, setName] = useState(coupon?.name ?? '');
  const [discountType, setDiscountType] = useState(coupon?.discount_type ?? 'percentage');
  const [discountValue, setDiscountValue] = useState(coupon?.discount_value ?? undefined);
  const [buyQuantity, setBuyQuantity] = useState(coupon?.buy_quantity ?? undefined);
  const [getQuantity, setGetQuantity] = useState(coupon?.get_quantity ?? undefined);
  const [minOrderAmount, setMinOrderAmount] = useState(coupon?.min_order_amount ?? undefined);
  const [maxDiscountAmount, setMaxDiscountAmount] = useState(coupon?.max_discount_amount ?? undefined);
  const [usageLimit, setUsageLimit] = useState(coupon?.usage_limit ?? undefined);
  const [usageLimitPerCustomer, setUsageLimitPerCustomer] = useState(coupon?.usage_limit_per_customer ?? undefined);
  const [expiresAt, setExpiresAt] = useState(coupon?.expires_at ? coupon.expires_at.slice(0, 16) : '');
  const [isActive, setIsActive] = useState(coupon?.is_active ?? true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!code.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        code: code.trim(),
        name: name.trim() || undefined,
        discount_type: discountType,
        discount_value: discountValue,
        buy_quantity: buyQuantity,
        get_quantity: getQuantity,
        min_order_amount: minOrderAmount,
        max_discount_amount: maxDiscountAmount,
        usage_limit: usageLimit,
        usage_limit_per_customer: usageLimitPerCustomer,
        expires_at: expiresAt ? new Date(expiresAt).toISOString() : undefined,
        is_active: isActive,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save coupon.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={coupon ? 'Edit coupon' : 'New coupon'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="max-h-[70vh] space-y-4 overflow-y-auto pr-1">
        <FormError message={error} />

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Code" htmlFor="coupon-code" />
            <FormInput id="coupon-code" autoFocus value={code} onChange={(e) => setCode(e.target.value)} required placeholder="SUMMER20" />
          </div>
          <div>
            <FormField label="Name (optional)" htmlFor="coupon-name" />
            <FormInput id="coupon-name" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
        </div>

        <div>
          <FormField label="Discount type" htmlFor="coupon-type" />
          <select id="coupon-type" value={discountType} onChange={(e) => setDiscountType(e.target.value as CouponDiscountType)} className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
            <option value="percentage">Percentage</option>
            <option value="fixed_amount">Flat amount</option>
            <option value="free_shipping">Free shipping</option>
            <option value="buy_x_get_y">Buy X, get Y</option>
          </select>
        </div>

        {discountType === 'percentage' || discountType === 'fixed_amount' ? (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <FormField label={discountType === 'percentage' ? 'Percentage (%)' : 'Amount'} htmlFor="coupon-value" />
              <FormInput id="coupon-value" type="number" step="0.01" value={discountValue ?? ''} onChange={(e) => setDiscountValue(e.target.value ? Number(e.target.value) : undefined)} />
            </div>
            {discountType === 'percentage' ? (
              <div>
                <FormField label="Max discount (optional)" htmlFor="coupon-max" />
                <FormInput id="coupon-max" type="number" step="0.01" value={maxDiscountAmount ?? ''} onChange={(e) => setMaxDiscountAmount(e.target.value ? Number(e.target.value) : undefined)} />
              </div>
            ) : null}
          </div>
        ) : null}

        {discountType === 'buy_x_get_y' ? (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <FormField label="Buy quantity" htmlFor="coupon-buy" />
              <FormInput id="coupon-buy" type="number" value={buyQuantity ?? ''} onChange={(e) => setBuyQuantity(e.target.value ? Number(e.target.value) : undefined)} />
            </div>
            <div>
              <FormField label="Get quantity free" htmlFor="coupon-get" />
              <FormInput id="coupon-get" type="number" value={getQuantity ?? ''} onChange={(e) => setGetQuantity(e.target.value ? Number(e.target.value) : undefined)} />
            </div>
          </div>
        ) : null}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Min order amount" htmlFor="coupon-min-order" />
            <FormInput id="coupon-min-order" type="number" step="0.01" value={minOrderAmount ?? ''} onChange={(e) => setMinOrderAmount(e.target.value ? Number(e.target.value) : undefined)} />
          </div>
          <div>
            <FormField label="Expires at" htmlFor="coupon-expires" />
            <FormInput id="coupon-expires" type="datetime-local" value={expiresAt} onChange={(e) => setExpiresAt(e.target.value)} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Usage limit (total)" htmlFor="coupon-usage" />
            <FormInput id="coupon-usage" type="number" value={usageLimit ?? ''} onChange={(e) => setUsageLimit(e.target.value ? Number(e.target.value) : undefined)} />
          </div>
          <div>
            <FormField label="Usage limit per customer" htmlFor="coupon-usage-customer" />
            <FormInput id="coupon-usage-customer" type="number" value={usageLimitPerCustomer ?? ''} onChange={(e) => setUsageLimitPerCustomer(e.target.value ? Number(e.target.value) : undefined)} />
          </div>
        </div>

        <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
          <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
          Active
        </label>

        <FormButton type="submit" loading={loading}>
          {coupon ? 'Save changes' : 'Create coupon'}
        </FormButton>
      </form>
    </Modal>
  );
}
