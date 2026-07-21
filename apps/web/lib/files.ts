import { apiFetch, ApiError } from '@/lib/api-client';
import type { BreadcrumbItem, FileItem, FileListResponse, FolderItem, SearchResponse } from '@/lib/types';

export async function listFiles(folderId: string | null): Promise<FileItem[]> {
  const query = folderId ? `?folder_id=${encodeURIComponent(folderId)}` : '';
  const data = await apiFetch<FileListResponse>(`/api/v1/files/${query}`);
  return data.files;
}

export async function listFolders(parentFolderId: string | null): Promise<FolderItem[]> {
  const query = parentFolderId ? `?parent_folder_id=${encodeURIComponent(parentFolderId)}` : '';
  return apiFetch<FolderItem[]>(`/api/v1/files/folders${query}`);
}

export async function getBreadcrumbs(folderId: string): Promise<BreadcrumbItem[]> {
  return apiFetch<BreadcrumbItem[]>(`/api/v1/files/folders/${folderId}/breadcrumbs`);
}

export async function createFolder(name: string, parentFolderId: string | null): Promise<FolderItem> {
  return apiFetch<FolderItem>('/api/v1/files/folders', {
    method: 'POST',
    json: { name, parent_folder_id: parentFolderId },
  });
}

export async function renameFolder(folderId: string, name: string): Promise<FolderItem> {
  return apiFetch<FolderItem>(`/api/v1/files/folders/${folderId}`, { method: 'PATCH', json: { name } });
}

export async function moveFolder(folderId: string, parentFolderId: string | null): Promise<FolderItem> {
  return apiFetch<FolderItem>(`/api/v1/files/folders/${folderId}`, {
    method: 'PATCH',
    json: parentFolderId ? { parent_folder_id: parentFolderId } : { move_to_root: true },
  });
}

export async function deleteFolder(folderId: string, recursive = false): Promise<void> {
  await apiFetch(`/api/v1/files/folders/${folderId}?recursive=${recursive}`, { method: 'DELETE' });
}

export interface UploadOptions {
  folderId?: string | null;
  visibility?: 'private' | 'public';
  allowDuplicate?: boolean;
}

export async function uploadFile(file: File, options: UploadOptions = {}): Promise<FileItem> {
  const formData = new FormData();
  formData.append('file', file);
  if (options.folderId) formData.append('folder_id', options.folderId);
  if (options.visibility) formData.append('visibility', options.visibility);
  formData.append('allow_duplicate', String(options.allowDuplicate ?? false));

  return apiFetch<FileItem>('/api/v1/files/upload', { method: 'POST', body: formData });
}

export async function renameFile(fileId: string, name: string): Promise<FileItem> {
  return apiFetch<FileItem>(`/api/v1/files/${fileId}`, { method: 'PATCH', json: { name } });
}

export async function moveFile(fileId: string, folderId: string | null): Promise<FileItem> {
  return apiFetch<FileItem>(`/api/v1/files/${fileId}/move`, { method: 'POST', json: { folder_id: folderId } });
}

export async function deleteFile(fileId: string): Promise<void> {
  await apiFetch(`/api/v1/files/${fileId}`, { method: 'DELETE' });
}

export async function getSignedUrl(fileId: string): Promise<string> {
  const data = await apiFetch<{ signed_url: string }>(`/api/v1/files/${fileId}/signed-url`);
  return data.signed_url;
}

export async function searchFiles(query: string): Promise<SearchResponse> {
  return apiFetch<SearchResponse>(`/api/v1/files/search?q=${encodeURIComponent(query)}`);
}

export { ApiError };
