'use client';

import { ArrowLeft as ArrowLeftIcon, ArrowRight as ArrowRightIcon, FileText, Star, Trash2, Upload, Video } from 'lucide-react';
import { useRef, useState } from 'react';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { deleteMedia, mediaDownloadUrl, reorderMedia, updateMedia, uploadMedia } from '@/lib/catalog/media';
import type { MediaItem } from '@/lib/types';

interface MediaGalleryProps {
  productId?: string;
  variantId?: string;
  items: MediaItem[];
  onChange: () => Promise<void> | void;
}

export function MediaGallery({ productId, variantId, items, onChange }: MediaGalleryProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return;
    setUploading(true);
    setError(null);
    try {
      for (const file of Array.from(fileList)) {
        const mediaType = file.type.startsWith('video/') ? 'video' : file.type === 'application/pdf' ? 'pdf' : 'image';
        await uploadMedia({ file, productId, variantId, mediaType, isPrimary: items.length === 0 });
      }
      await onChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to upload media.');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleSetPrimary = async (media: MediaItem) => {
    await updateMedia(media.id, { is_primary: true });
    await onChange();
  };

  const handleDelete = async (media: MediaItem) => {
    if (!confirm('Delete this media item?')) return;
    await deleteMedia(media.id);
    await onChange();
  };

  const handleMove = async (index: number, direction: -1 | 1) => {
    const targetIndex = index + direction;
    if (targetIndex < 0 || targetIndex >= items.length) return;
    const reordered = [...items];
    [reordered[index], reordered[targetIndex]] = [reordered[targetIndex], reordered[index]];
    await reorderMedia(reordered.map((m) => m.id));
    await onChange();
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-slate-900 dark:text-white">Media</h3>
        <PermissionGuard permission="catalog.media.manage">
          <label className="flex cursor-pointer items-center gap-2 rounded-xl bg-cyan-500 px-3 py-1.5 text-xs font-semibold text-slate-950 transition hover:bg-cyan-400">
            <Upload size={14} />
            {uploading ? 'Uploading…' : 'Upload'}
            <input ref={fileInputRef} type="file" multiple accept="image/*,video/*,application/pdf" className="hidden" onChange={(e) => handleUpload(e.target.files)} />
          </label>
        </PermissionGuard>
      </div>

      {error ? <p className="text-sm text-red-600 dark:text-red-400">{error}</p> : null}

      {items.length === 0 ? (
        <EmptyState title="No media yet" description="Upload images, videos, or PDFs for this product." />
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
          {items.map((media, index) => (
            <div key={media.id} className="group relative overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800">
              {media.media_type === 'image' ? (
                <img src={mediaDownloadUrl(media.id)} alt={media.alt_text ?? ''} className="h-28 w-full object-cover" />
              ) : (
                <div className="flex h-28 w-full items-center justify-center bg-slate-100 text-slate-400 dark:bg-slate-900">
                  {media.media_type === 'video' ? <Video size={24} /> : <FileText size={24} />}
                </div>
              )}
              {media.is_primary ? (
                <span className="absolute left-1.5 top-1.5 rounded-full bg-amber-400 p-1 text-slate-900">
                  <Star size={12} className="fill-slate-900" />
                </span>
              ) : null}
              <PermissionGuard permission="catalog.media.manage">
                <div className="absolute inset-x-0 bottom-0 flex items-center justify-between bg-black/60 px-1.5 py-1 opacity-0 transition group-hover:opacity-100">
                  <div className="flex gap-1">
                    <button type="button" onClick={() => handleMove(index, -1)} className="rounded p-0.5 text-white hover:bg-white/20"><ArrowLeftIcon size={12} /></button>
                    <button type="button" onClick={() => handleMove(index, 1)} className="rounded p-0.5 text-white hover:bg-white/20"><ArrowRightIcon size={12} /></button>
                  </div>
                  <div className="flex gap-1">
                    {!media.is_primary ? (
                      <button type="button" onClick={() => handleSetPrimary(media)} className="rounded p-0.5 text-white hover:bg-white/20"><Star size={12} /></button>
                    ) : null}
                    <button type="button" onClick={() => handleDelete(media)} className="rounded p-0.5 text-red-300 hover:bg-white/20"><Trash2 size={12} /></button>
                  </div>
                </div>
              </PermissionGuard>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
