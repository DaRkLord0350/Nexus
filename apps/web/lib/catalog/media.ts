import { API_BASE, apiFetch, getAccessToken } from '@/lib/api-client';
import type { MediaItem, MediaListResponse } from '@/lib/types';

export async function fetchMediaForProduct(productId: string): Promise<MediaListResponse> {
  return apiFetch<MediaListResponse>(`/api/v1/catalog/media/product/${productId}`);
}

export async function fetchMediaForVariant(variantId: string): Promise<MediaListResponse> {
  return apiFetch<MediaListResponse>(`/api/v1/catalog/media/variant/${variantId}`);
}

export async function uploadMedia(params: {
  file: File;
  productId?: string;
  variantId?: string;
  mediaType?: string;
  altText?: string;
  isPrimary?: boolean;
}): Promise<MediaItem> {
  const formData = new FormData();
  formData.append('file', params.file);
  if (params.productId) formData.append('product_id', params.productId);
  if (params.variantId) formData.append('variant_id', params.variantId);
  formData.append('media_type', params.mediaType ?? 'image');
  if (params.altText) formData.append('alt_text', params.altText);
  formData.append('is_primary', String(params.isPrimary ?? false));

  const token = getAccessToken();
  const response = await fetch(`${API_BASE}/api/v1/catalog/media/upload`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    body: formData,
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail ?? 'Unable to upload media.');
  }
  return response.json();
}

export async function updateMedia(mediaId: string, data: { alt_text?: string; is_primary?: boolean; sort_order?: number }): Promise<MediaItem> {
  return apiFetch<MediaItem>(`/api/v1/catalog/media/${mediaId}`, { method: 'PATCH', json: data });
}

export async function deleteMedia(mediaId: string): Promise<void> {
  await apiFetch(`/api/v1/catalog/media/${mediaId}`, { method: 'DELETE' });
}

export async function reorderMedia(mediaIds: string[]): Promise<void> {
  await apiFetch(`/api/v1/catalog/media/reorder`, { method: 'POST', json: { media_ids: mediaIds } });
}

export function mediaDownloadUrl(mediaId: string): string {
  return `${API_BASE}/api/v1/catalog/media/${mediaId}/download`;
}
