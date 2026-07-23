import { getOrCreateGuestSessionToken, portalApiFetch, withOrg } from '@/lib/customer-portal/api-client';

export interface CartItemRead {
  id: string;
  cart_id: string;
  product_id: string;
  variant_id?: string | null;
  quantity: number;
  unit_price: number;
  saved_for_later: boolean;
  gift_note?: string | null;
  line_total: number;
}

export interface CartRead {
  id: string;
  customer_id?: string | null;
  session_token?: string | null;
  status: string;
  currency: string;
  coupon_code?: string | null;
  subtotal: number;
  discount_amount: number;
  tax_amount: number;
  shipping_amount: number;
  total: number;
  order_id?: string | null;
}

export interface CartDetail extends CartRead {
  items: CartItemRead[];
}

function sessionTokenIfGuest(cart?: CartDetail | CartRead | null): string | undefined {
  if (cart?.customer_id) return undefined;
  return getOrCreateGuestSessionToken();
}

export async function getOrCreateMyCart(currency = 'USD'): Promise<CartDetail> {
  return portalApiFetch<CartDetail>(withOrg('/api/v1/cart/'), {
    method: 'POST',
    json: { session_token: getOrCreateGuestSessionToken(), currency },
  });
}

export async function fetchCart(cartId: string, cart?: CartRead | null): Promise<CartDetail> {
  return portalApiFetch<CartDetail>(withOrg(`/api/v1/cart/${cartId}`, { session_token: sessionTokenIfGuest(cart) }));
}

export async function addCartItem(cartId: string, cart: CartRead | null, productId: string, quantity: number, variantId?: string): Promise<CartItemRead> {
  return portalApiFetch<CartItemRead>(withOrg(`/api/v1/cart/${cartId}/items`, { session_token: sessionTokenIfGuest(cart) }), {
    method: 'POST',
    json: { product_id: productId, variant_id: variantId, quantity },
  });
}

export async function updateCartItem(cartId: string, cart: CartRead | null, itemId: string, quantity: number): Promise<CartItemRead> {
  return portalApiFetch<CartItemRead>(withOrg(`/api/v1/cart/${cartId}/items/${itemId}`, { session_token: sessionTokenIfGuest(cart) }), {
    method: 'PATCH',
    json: { quantity },
  });
}

export async function removeCartItem(cartId: string, cart: CartRead | null, itemId: string): Promise<void> {
  await portalApiFetch(withOrg(`/api/v1/cart/${cartId}/items/${itemId}`, { session_token: sessionTokenIfGuest(cart) }), { method: 'DELETE' });
}

export async function applyCartCoupon(cartId: string, cart: CartRead | null, code: string): Promise<CartRead> {
  return portalApiFetch<CartRead>(withOrg(`/api/v1/cart/${cartId}/coupon`, { session_token: sessionTokenIfGuest(cart) }), {
    method: 'POST',
    json: { code },
  });
}

export async function removeCartCoupon(cartId: string, cart: CartRead | null): Promise<CartRead> {
  return portalApiFetch<CartRead>(withOrg(`/api/v1/cart/${cartId}/coupon`, { session_token: sessionTokenIfGuest(cart) }), { method: 'DELETE' });
}

export async function mergeGuestCartIntoMine(): Promise<CartDetail> {
  return portalApiFetch<CartDetail>(withOrg('/api/v1/cart/merge'), {
    method: 'POST',
    json: { session_token: getOrCreateGuestSessionToken() },
  });
}
