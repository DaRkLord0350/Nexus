'use client';

import { useState } from 'react';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import { Modal } from '@/components/ui/modal';
import type { OrderCreateInput } from '@/lib/orders/orders';

interface OrderFormModalProps {
  onSubmit: (data: OrderCreateInput) => Promise<void>;
  onClose: () => void;
}

export function OrderFormModal({ onSubmit, onClose }: OrderFormModalProps) {
  const [customerId, setCustomerId] = useState('');
  const [productId, setProductId] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [unitPrice, setUnitPrice] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('cod');
  const [shippingMethod, setShippingMethod] = useState('standard');
  const [shippingAmount, setShippingAmount] = useState('0');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [line1, setLine1] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [postalCode, setPostalCode] = useState('');
  const [country, setCountry] = useState('US');
  const [sameAsBilling, setSameAsBilling] = useState(true);
  const [shipFirstName, setShipFirstName] = useState('');
  const [shipLastName, setShipLastName] = useState('');
  const [shipLine1, setShipLine1] = useState('');
  const [shipCity, setShipCity] = useState('');
  const [shipState, setShipState] = useState('');
  const [shipPostalCode, setShipPostalCode] = useState('');
  const [shipCountry, setShipCountry] = useState('US');
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    setError(null);
    if (!customerId.trim() || !productId.trim() || !firstName.trim() || !lastName.trim() || !line1.trim() || !city.trim()) {
      setError('Please fill in the required fields.');
      return;
    }
    setSaving(true);
    try {
      const billing = { first_name: firstName, last_name: lastName, line1, city, state: state || undefined, postal_code: postalCode || undefined, country };
      const shipping = sameAsBilling
        ? billing
        : { first_name: shipFirstName, last_name: shipLastName, line1: shipLine1, city: shipCity, state: shipState || undefined, postal_code: shipPostalCode || undefined, country: shipCountry };

      await onSubmit({
        customer_id: customerId.trim(),
        billing_address: billing,
        shipping_address: shipping,
        payment_method: paymentMethod,
        shipping_method: shippingMethod,
        shipping_amount: Number(shippingAmount) || 0,
        items: [{ product_id: productId.trim(), quantity: Number(quantity) || 1, unit_price: unitPrice ? Number(unitPrice) : undefined }],
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create order.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title="New order" onClose={onClose}>
      <div className="max-h-[70vh] space-y-4 overflow-y-auto pr-1">
        <div>
          <FormField label="Customer ID" htmlFor="customer_id" />
          <FormInput id="customer_id" value={customerId} onChange={(e) => setCustomerId(e.target.value)} placeholder="Customer ID" />
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <FormField label="Product ID" htmlFor="product_id" />
            <FormInput id="product_id" value={productId} onChange={(e) => setProductId(e.target.value)} />
          </div>
          <div>
            <FormField label="Quantity" htmlFor="quantity" />
            <FormInput id="quantity" type="number" min={1} value={quantity} onChange={(e) => setQuantity(e.target.value)} />
          </div>
          <div>
            <FormField label="Unit price (optional)" htmlFor="unit_price" />
            <FormInput id="unit_price" type="number" min={0} step="0.01" value={unitPrice} onChange={(e) => setUnitPrice(e.target.value)} placeholder="Auto" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <FormField label="Payment method" htmlFor="payment_method" />
            <select id="payment_method" value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)} className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
              <option value="cod">Cash on delivery</option>
              <option value="card">Card</option>
              <option value="wallet">Wallet</option>
              <option value="bank_transfer">Bank transfer</option>
            </select>
          </div>
          <div>
            <FormField label="Shipping method" htmlFor="shipping_method" />
            <select id="shipping_method" value={shippingMethod} onChange={(e) => setShippingMethod(e.target.value)} className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
              <option value="standard">Standard</option>
              <option value="express">Express</option>
            </select>
          </div>
        </div>

        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Billing address</p>
        <div className="grid grid-cols-2 gap-3">
          <FormInput placeholder="First name" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
          <FormInput placeholder="Last name" value={lastName} onChange={(e) => setLastName(e.target.value)} />
        </div>
        <FormInput placeholder="Address line 1" value={line1} onChange={(e) => setLine1(e.target.value)} />
        <div className="grid grid-cols-3 gap-3">
          <FormInput placeholder="City" value={city} onChange={(e) => setCity(e.target.value)} />
          <FormInput placeholder="State" value={state} onChange={(e) => setState(e.target.value)} />
          <FormInput placeholder="Postal code" value={postalCode} onChange={(e) => setPostalCode(e.target.value)} />
        </div>
        <FormInput placeholder="Country (2-letter)" maxLength={2} value={country} onChange={(e) => setCountry(e.target.value.toUpperCase())} />

        <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
          <input type="checkbox" checked={sameAsBilling} onChange={(e) => setSameAsBilling(e.target.checked)} />
          Shipping address same as billing
        </label>

        {!sameAsBilling ? (
          <>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Shipping address</p>
            <div className="grid grid-cols-2 gap-3">
              <FormInput placeholder="First name" value={shipFirstName} onChange={(e) => setShipFirstName(e.target.value)} />
              <FormInput placeholder="Last name" value={shipLastName} onChange={(e) => setShipLastName(e.target.value)} />
            </div>
            <FormInput placeholder="Address line 1" value={shipLine1} onChange={(e) => setShipLine1(e.target.value)} />
            <div className="grid grid-cols-3 gap-3">
              <FormInput placeholder="City" value={shipCity} onChange={(e) => setShipCity(e.target.value)} />
              <FormInput placeholder="State" value={shipState} onChange={(e) => setShipState(e.target.value)} />
              <FormInput placeholder="Postal code" value={shipPostalCode} onChange={(e) => setShipPostalCode(e.target.value)} />
            </div>
            <FormInput placeholder="Country (2-letter)" maxLength={2} value={shipCountry} onChange={(e) => setShipCountry(e.target.value.toUpperCase())} />
          </>
        ) : null}

        <FormError message={error} />
        <FormButton type="button" loading={saving} onClick={handleSubmit}>
          Create order
        </FormButton>
      </div>
    </Modal>
  );
}
