'use client';

import { File as FileIcon, FileText, Image as ImageIcon, Lock, Globe } from 'lucide-react';
import { ItemMenu, type ItemMenuAction } from '@/components/files/item-menu';
import { formatBytes } from '@/lib/format';
import type { FileItem } from '@/lib/types';

function iconFor(contentType: string) {
  if (contentType.startsWith('image/')) return ImageIcon;
  if (contentType === 'application/pdf' || contentType.includes('word')) return FileText;
  return FileIcon;
}

interface FileCardProps {
  file: FileItem;
  onOpen: () => void;
  onRename: () => void;
  onDelete: () => void;
  onMoveToRoot: () => void;
}

export function FileCard({ file, onOpen, onRename, onDelete, onMoveToRoot }: FileCardProps) {
  const Icon = iconFor(file.content_type);
  const actions: ItemMenuAction[] = [
    { label: 'Rename', onSelect: onRename },
  ];
  if (file.folder_id) {
    actions.push({ label: 'Move to root', onSelect: onMoveToRoot });
  }
  actions.push({ label: 'Delete', onSelect: onDelete, danger: true });

  return (
    <div
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData('text/x-file-id', file.id);
        e.dataTransfer.effectAllowed = 'move';
      }}
      onClick={onOpen}
      className="group flex cursor-pointer items-center justify-between gap-2 rounded-2xl border border-slate-200 bg-white p-4 transition hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900/60 dark:hover:border-slate-700"
    >
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-600 dark:text-cyan-300">
          <Icon size={18} />
        </div>
        <div className="min-w-0">
          <p className="flex items-center gap-1.5 truncate text-sm font-medium text-slate-900 dark:text-white">
            {file.name}
            {file.visibility === 'public' ? (
              <Globe size={12} className="shrink-0 text-emerald-500" />
            ) : (
              <Lock size={12} className="shrink-0 text-slate-400" />
            )}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400">{formatBytes(file.size_bytes)}</p>
        </div>
      </div>
      <ItemMenu actions={actions} />
    </div>
  );
}
