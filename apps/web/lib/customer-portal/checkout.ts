import { getOrCreateGuestSessionToken, portalApiFetch, withOrg } from '@/lib/customer-portal/api-client';
import type { OrderRead } from '@/lib/types';

export interface CheckoutAddressInput {
  first_name: string;
  last_name: string;
  company?: string;
  phone?: string;
  line1: string;
  line2?: string;
  city: string;
  state?: string;
  postal_code?: string;
  country: string;
}

export interface CheckoutQuoteResult {
  currency: string;
  subtotal: number;
  discount_amount: number;
  tax_amount: number;
  shipping_amount: number;
  total: number;
}

export interface CheckoutInput {
  cart_id: string;
  isGuest: boolean;
  guest_email?: string;
  guest_first_name?: string;
  guest_last_name?: string;
  billing_address_id?: string;
  billing_address?: CheckoutAddressInput;
  shipping_address_id?: string;
  shipping_address?: CheckoutAddressInput;
  save_addresses?: boolean;
  payment_method: string;
  shipping_method: string;
  customer_note?: string;
  gift_note?: string;
}

export async function getCheckoutQuote(cartId: string, isGuest: boolean, country: string, state?: string, shippingMethod = 'standard'): Promise<CheckoutQuoteResult> {
  return portalApiFetch<CheckoutQuoteResult>(withOrg('/api/v1/checkout/quote'), {
    method: 'POST',
    json: {
      cart_id: cartId,
      session_token: isGuest ? getOrCreateGuestSessionToken() : undefined,
      country,
      state,
      shipping_method: shippingMethod,
    },
  });
}

export async function submitCheckout(data: CheckoutInput): Promise<OrderRead> {
  return portalApiFetch<OrderRead>(withOrg('/api/v1/checkout/'), {
    method: 'POST',
    json: {
      cart_id: data.cart_id,
      session_token: data.isGuest ? getOrCreateGuestSessionToken() : undefined,
      guest_email: data.guest_email,
      guest_first_name: data.guest_first_name,
      guest_last_name: data.guest_last_name,
      billing_address_id: data.billing_address_id,
      billing_address: data.billing_address,
      shipping_address_id: data.shipping_address_id,
      shipping_address: data.shipping_address,
      save_addresses: data.save_addresses ?? false,
      payment_method: data.payment_method,
      shipping_method: data.shipping_method,
      customer_note: data.customer_note,
      gift_note: data.gift_note,
    },
  });
}
