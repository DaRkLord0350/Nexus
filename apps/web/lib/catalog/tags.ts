import { apiFetch } from '@/lib/api-client';
import type { TagItem, TagListResponse } from '@/lib/types';

export interface TagCreateInput {
  name: string;
  slug?: string;
}

export type TagUpdateInput = Partial<TagCreateInput>;

export async function fetchTags(q?: string, limit = 100): Promise<TagListResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (q) params.set('q', q);
  return apiFetch<TagListResponse>(`/api/v1/catalog/tags/?${params.toString()}`);
}

export async function createTag(data: TagCreateInput): Promise<TagItem> {
  return apiFetch<TagItem>('/api/v1/catalog/tags/', { method: 'POST', json: data });
}

export async function updateTag(tagId: string, data: TagUpdateInput): Promise<TagItem> {
  return apiFetch<TagItem>(`/api/v1/catalog/tags/${tagId}`, { method: 'PATCH', json: data });
}

export async function deleteTag(tagId: string): Promise<void> {
  await apiFetch(`/api/v1/catalog/tags/${tagId}`, { method: 'DELETE' });
}
