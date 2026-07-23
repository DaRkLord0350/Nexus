'use client';

import { CheckCircle2 } from 'lucide-react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useState } from 'react';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import { getCustomerToken } from '@/lib/customer-portal/api-client';
import { submitCheckout } from '@/lib/customer-portal/checkout';
import type { OrderRead } from '@/lib/types';

export default function ShopCheckoutPage() {
  const searchParams = useSearchParams();
  const cartId = searchParams.get('cartId') ?? '';
  const isGuest = typeof window !== 'undefined' ? !getCustomerToken() : true;

  const [guestEmail, setGuestEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [line1, setLine1] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [postalCode, setPostalCode] = useState('');
  const [country, setCountry] = useState('US');
  const [paymentMethod, setPaymentMethod] = useState('cod');
  const [shippingMethod, setShippingMethod] = useState('standard');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmedOrder, setConfirmedOrder] = useState<OrderRead | null>(null);

  const handleSubmit = async () => {
    setError(null);
    if (!cartId) {
      setError('Missing cart. Please return to your cart and try again.');
      return;
    }
    if (!firstName.trim() || !lastName.trim() || !line1.trim() || !city.trim()) {
      setError('Please complete the address fields.');
      return;
    }
    if (isGuest && !guestEmail.trim()) {
      setError('Please provide an email address.');
      return;
    }
    setSaving(true);
    try {
      const address = { first_name: firstName, last_name: lastName, line1, city, state: state || undefined, postal_code: postalCode || undefined, country };
      const order = await submitCheckout({
        cart_id: cartId,
        isGuest,
        guest_email: isGuest ? guestEmail.trim() : undefined,
        guest_first_name: isGuest ? firstName : undefined,
        guest_last_name: isGuest ? lastName : undefined,
        billing_address: address,
        shipping_address: address,
        payment_method: paymentMethod,
        shipping_method: shippingMethod,
      });
      setConfirmedOrder(order);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to place your order.');
    } finally {
      setSaving(false);
    }
  };

  if (confirmedOrder) {
    return (
      <div className="space-y-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-8 text-center dark:border-emerald-500/30 dark:bg-emerald-500/10">
        <CheckCircle2 className="mx-auto text-emerald-600 dark:text-emerald-400" size={40} />
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Order confirmed!</h2>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Your order <strong>{confirmedOrder.order_number}</strong> for {confirmedOrder.currency} {confirmedOrder.total.toFixed(2)} has been placed.
        </p>
        {!isGuest ? (
          <Link href={`/portal/dashboard/orders/${confirmedOrder.id}`} className="inline-block rounded-xl bg-cyan-500 px-4 py-2.5 text-sm font-semibold text-slate-950 hover:bg-cyan-400">
            View order
          </Link>
        ) : (
          <p className="text-sm text-slate-500 dark:text-slate-400">A confirmation has been recorded under {guestEmail}.</p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Checkout</h2>
      <FormError message={error} />

      <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
        {isGuest ? (
          <div>
            <FormField label="Email" htmlFor="guest_email" />
            <FormInput id="guest_email" type="email" value={guestEmail} onChange={(e) => setGuestEmail(e.target.value)} />
          </div>
        ) : null}

        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Shipping address</p>
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

        <div className="grid grid-cols-2 gap-3">
          <div>
            <FormField label="Payment method" htmlFor="payment_method" />
            <select id="payment_method" value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)} className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
              <option value="cod">Cash on delivery</option>
              <option value="card">Card</option>
              <option value="wallet">Wallet</option>
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

        <FormButton type="button" loading={saving} onClick={handleSubmit}>
          Place order
        </FormButton>
      </div>
    </div>
  );
}
