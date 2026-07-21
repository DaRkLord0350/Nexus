'use client';

import { FolderOpen, FolderPlus, Search } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { PermissionGuard } from '@/components/permission-guard';
import { FileBreadcrumbs } from '@/components/files/breadcrumbs';
import { FileCard } from '@/components/files/file-card';
import { FilePreviewModal } from '@/components/files/file-preview-modal';
import { FolderCard } from '@/components/files/folder-card';
import { NamePromptModal } from '@/components/files/name-prompt-modal';
import { UploadDropzone } from '@/components/files/upload-dropzone';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { ApiError } from '@/lib/api-client';
import {
  createFolder,
  deleteFile,
  deleteFolder,
  getBreadcrumbs,
  listFiles,
  listFolders,
  moveFile,
  renameFile,
  renameFolder,
  searchFiles,
  uploadFile,
} from '@/lib/files';
import type { BreadcrumbItem, FileItem, FolderItem, SearchResponse } from '@/lib/types';

type RenameTarget = { type: 'file' | 'folder'; id: string; name: string };

export default function FilesPage() {
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null);
  const [breadcrumbs, setBreadcrumbs] = useState<BreadcrumbItem[]>([]);
  const [folders, setFolders] = useState<FolderItem[]>([]);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);

  const [previewFile, setPreviewFile] = useState<FileItem | null>(null);
  const [renameTarget, setRenameTarget] = useState<RenameTarget | null>(null);
  const [newFolderOpen, setNewFolderOpen] = useState(false);

  const loadFolder = useCallback(async (folderId: string | null) => {
    setLoading(true);
    setError(null);
    try {
      const [folderFiles, childFolders, crumbs] = await Promise.all([
        listFiles(folderId),
        listFolders(folderId),
        folderId ? getBreadcrumbs(folderId) : Promise.resolve([]),
      ]);
      setFiles(folderFiles);
      setFolders(childFolders);
      setBreadcrumbs(crumbs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load files.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFolder(currentFolderId);
  }, [currentFolderId, loadFolder]);

  const handleNavigate = (folderId: string | null) => {
    setSearchQuery('');
    setSearchResults(null);
    setCurrentFolderId(folderId);
  };

  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    if (!query.trim()) {
      setSearchResults(null);
      return;
    }
    try {
      const results = await searchFiles(query.trim());
      setSearchResults(results);
    } catch {
      setError('Search failed.');
    }
  };

  const handleFilesSelected = async (fileList: FileList) => {
    setUploading(true);
    setError(null);
    try {
      for (const file of Array.from(fileList)) {
        try {
          await uploadFile(file, { folderId: currentFolderId });
        } catch (err) {
          if (err instanceof ApiError && err.status === 409) {
            const detail = err.detail as { message?: string } | string;
            const message = typeof detail === 'string' ? detail : detail?.message;
            const confirmed = window.confirm(`${message || 'A duplicate file already exists.'} Upload anyway?`);
            if (confirmed) {
              await uploadFile(file, { folderId: currentFolderId, allowDuplicate: true });
            }
          } else {
            throw err;
          }
        }
      }
      await loadFolder(currentFolderId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const handleCreateFolder = async (name: string) => {
    await createFolder(name, currentFolderId);
    await loadFolder(currentFolderId);
  };

  const handleRenameSubmit = async (value: string) => {
    if (!renameTarget) return;
    if (renameTarget.type === 'file') {
      await renameFile(renameTarget.id, value);
    } else {
      await renameFolder(renameTarget.id, value);
    }
    await loadFolder(currentFolderId);
  };

  const handleDeleteFile = async (fileId: string) => {
    if (!window.confirm('Delete this file? This cannot be undone.')) return;
    await deleteFile(fileId);
    await loadFolder(currentFolderId);
  };

  const handleDeleteFolder = async (folderId: string) => {
    if (!window.confirm('Delete this folder?')) return;
    try {
      await deleteFolder(folderId, false);
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        const forceDelete = window.confirm('This folder is not empty. Delete it and everything inside?');
        if (!forceDelete) return;
        await deleteFolder(folderId, true);
      } else {
        throw err;
      }
    }
    await loadFolder(currentFolderId);
  };

  const handleMoveFileToFolder = async (fileId: string, folderId: string) => {
    await moveFile(fileId, folderId);
    await loadFolder(currentFolderId);
  };

  const handleMoveFileToRoot = async (fileId: string) => {
    await moveFile(fileId, null);
    await loadFolder(currentFolderId);
  };

  const isSearching = searchResults !== null;
  const visibleFolders = isSearching ? searchResults.folders : folders;
  const visibleFiles = isSearching ? searchResults.files : files;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        {isSearching ? (
          <p className="text-sm font-medium text-slate-700 dark:text-slate-200">
            Search results for &quot;{searchQuery}&quot;
          </p>
        ) : (
          <FileBreadcrumbs items={breadcrumbs} onNavigate={handleNavigate} />
        )}

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Search files & folders"
              className="w-56 rounded-xl border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white dark:placeholder:text-slate-500"
            />
          </div>
          <PermissionGuard permission="files">
            <button
              type="button"
              onClick={() => setNewFolderOpen(true)}
              className="flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              <FolderPlus size={16} />
              New folder
            </button>
          </PermissionGuard>
        </div>
      </div>

      <FormError message={error} />

      {!isSearching ? (
        <PermissionGuard permission="files">
          <UploadDropzone onFiles={handleFilesSelected} uploading={uploading} />
        </PermissionGuard>
      ) : null}

      {loading ? (
        <SkeletonRows count={4} />
      ) : visibleFolders.length === 0 && visibleFiles.length === 0 ? (
        <EmptyState
          icon={FolderOpen}
          title={isSearching ? 'No matches found' : 'This folder is empty'}
          description={isSearching ? 'Try a different search term.' : 'Upload a file or create a folder to get started.'}
        />
      ) : (
        <div className="space-y-6">
          {visibleFolders.length > 0 ? (
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Folders</p>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {visibleFolders.map((folder) => (
                  <FolderCard
                    key={folder.id}
                    folder={folder}
                    onOpen={() => handleNavigate(folder.id)}
                    onRename={() => setRenameTarget({ type: 'folder', id: folder.id, name: folder.name })}
                    onDelete={() => handleDeleteFolder(folder.id)}
                    onDropFile={(fileId) => handleMoveFileToFolder(fileId, folder.id)}
                  />
                ))}
              </div>
            </div>
          ) : null}

          {visibleFiles.length > 0 ? (
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Files</p>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {visibleFiles.map((file) => (
                  <FileCard
                    key={file.id}
                    file={file}
                    onOpen={() => setPreviewFile(file)}
                    onRename={() => setRenameTarget({ type: 'file', id: file.id, name: file.name })}
                    onDelete={() => handleDeleteFile(file.id)}
                    onMoveToRoot={() => handleMoveFileToRoot(file.id)}
                  />
                ))}
              </div>
            </div>
          ) : null}
        </div>
      )}

      {previewFile ? <FilePreviewModal file={previewFile} onClose={() => setPreviewFile(null)} /> : null}

      {renameTarget ? (
        <NamePromptModal
          title={`Rename ${renameTarget.type}`}
          initialValue={renameTarget.name}
          submitLabel="Rename"
          onSubmit={handleRenameSubmit}
          onClose={() => setRenameTarget(null)}
        />
      ) : null}

      {newFolderOpen ? (
        <NamePromptModal
          title="New folder"
          submitLabel="Create"
          onSubmit={handleCreateFolder}
          onClose={() => setNewFolderOpen(false)}
        />
      ) : null}
    </div>
  );
}
