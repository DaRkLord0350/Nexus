'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { ProductPriceCreateInput } from '@/lib/catalog/pricing';
import type { ProductPriceItem } from '@/lib/types';

interface PriceFormModalProps {
  productId: string;
  price?: ProductPriceItem | null;
  onSubmit: (data: ProductPriceCreateInput) => Promise<void>;
  onClose: () => void;
}

export function PriceFormModal({ productId, price, onSubmit, onClose }: PriceFormModalProps) {
  const [currency, setCurrency] = useState(price?.currency ?? 'USD');
  const [sellingPrice, setSellingPrice] = useState(price?.selling_price ?? 0);
  const [mrp, setMrp] = useState(price?.mrp ?? undefined);
  const [comparePrice, setComparePrice] = useState(price?.compare_price ?? undefined);
  const [costPrice, setCostPrice] = useState(price?.cost_price ?? undefined);
  const [region, setRegion] = useState(price?.region ?? '');
  const [customerGroup, setCustomerGroup] = useState(price?.customer_group ?? '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await onSubmit({
        product_id: productId,
        currency: currency.trim().toUpperCase(),
        selling_price: sellingPrice,
        mrp,
        compare_price: comparePrice,
        cost_price: costPrice,
        region: region.trim() || undefined,
        customer_group: customerGroup.trim() || undefined,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save price.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={price ? 'Edit price' : 'New price'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormError message={error} />

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Currency" htmlFor="price-currency" />
            <FormInput id="price-currency" maxLength={3} value={currency} onChange={(e) => setCurrency(e.target.value)} required />
          </div>
          <div>
            <FormField label="Selling price" htmlFor="price-selling" />
            <FormInput id="price-selling" type="number" step="0.01" value={sellingPrice} onChange={(e) => setSellingPrice(Number(e.target.value) || 0)} required />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="MRP" htmlFor="price-mrp" />
            <FormInput id="price-mrp" type="number" step="0.01" value={mrp ?? ''} onChange={(e) => setMrp(e.target.value ? Number(e.target.value) : undefined)} />
          </div>
          <div>
            <FormField label="Compare-at price" htmlFor="price-compare" />
            <FormInput id="price-compare" type="number" step="0.01" value={comparePrice ?? ''} onChange={(e) => setComparePrice(e.target.value ? Number(e.target.value) : undefined)} />
          </div>
        </div>

        <div>
          <FormField label="Cost price" htmlFor="price-cost" />
          <FormInput id="price-cost" type="number" step="0.01" value={costPrice ?? ''} onChange={(e) => setCostPrice(e.target.value ? Number(e.target.value) : undefined)} />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <FormField label="Region (optional)" htmlFor="price-region" />
            <FormInput id="price-region" placeholder="e.g. IN, US" value={region} onChange={(e) => setRegion(e.target.value)} />
          </div>
          <div>
            <FormField label="Customer group (optional)" htmlFor="price-group" />
            <FormInput id="price-group" placeholder="e.g. wholesale" value={customerGroup} onChange={(e) => setCustomerGroup(e.target.value)} />
          </div>
        </div>

        <FormButton type="submit" loading={loading}>
          {price ? 'Save changes' : 'Add price'}
        </FormButton>
      </form>
    </Modal>
  );
}
