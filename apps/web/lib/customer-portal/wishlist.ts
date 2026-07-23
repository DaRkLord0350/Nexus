import { portalApiFetch, withOrg } from '@/lib/customer-portal/api-client';

export interface WishlistItem {
  id: string;
  customer_id: string;
  product_id: string;
  variant_id?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface WishlistListResponse {
  items: WishlistItem[];
  total: number;
  limit: number;
  offset: number;
}

export async function fetchMyWishlist(limit = 50, offset = 0): Promise<WishlistListResponse> {
  return portalApiFetch<WishlistListResponse>(withOrg('/api/v1/wishlist/', { limit: String(limit), offset: String(offset) }));
}

export async function removeMyWishlistItem(itemId: string): Promise<void> {
  await portalApiFetch(withOrg(`/api/v1/wishlist/${itemId}`), { method: 'DELETE' });
}

export async function moveMyWishlistItemToCart(itemId: string, sessionToken?: string, quantity = 1) {
  return portalApiFetch(withOrg(`/api/v1/wishlist/${itemId}/move-to-cart`, { session_token: sessionToken, quantity: String(quantity) }), { method: 'POST' });
}
