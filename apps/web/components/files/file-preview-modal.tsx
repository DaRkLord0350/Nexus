'use client';

import { Download } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Modal } from '@/components/ui/modal';
import { getSignedUrl } from '@/lib/files';
import { formatBytes } from '@/lib/format';
import type { FileItem } from '@/lib/types';

export function FilePreviewModal({ file, onClose }: { file: FileItem; onClose: () => void }) {
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSignedUrl(file.id)
      .then(setUrl)
      .catch(() => setError('Unable to load a preview link for this file.'));
  }, [file.id]);

  const isImage = file.content_type.startsWith('image/');
  const isPdf = file.content_type === 'application/pdf';

  return (
    <Modal title={file.name} onClose={onClose}>
      <div className="space-y-4">
        <div className="flex items-center justify-between text-sm text-slate-500 dark:text-slate-400">
          <span>{file.content_type}</span>
          <span>{formatBytes(file.size_bytes)}</span>
        </div>

        {error ? <p className="text-sm text-red-500">{error}</p> : null}

        {url && isImage ? (
          <img src={url} alt={file.name} className="max-h-96 w-full rounded-2xl object-contain" />
        ) : url && isPdf ? (
          <iframe src={url} title={file.name} className="h-96 w-full rounded-2xl border border-slate-200 dark:border-slate-800" />
        ) : (
          <div className="flex h-32 items-center justify-center rounded-2xl border border-dashed border-slate-300 text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
            No inline preview available for this file type.
          </div>
        )}

        {url ? (
          <a
            href={url}
            target="_blank"
            rel="noreferrer"
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-500 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400"
          >
            <Download size={16} />
            Download
          </a>
        ) : null}
      </div>
    </Modal>
  );
}
