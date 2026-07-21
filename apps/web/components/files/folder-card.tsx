'use client';

import { Folder } from 'lucide-react';
import { useState } from 'react';
import { ItemMenu } from '@/components/files/item-menu';
import type { FolderItem } from '@/lib/types';

interface FolderCardProps {
  folder: FolderItem;
  onOpen: () => void;
  onRename: () => void;
  onDelete: () => void;
  onDropFile: (fileId: string) => void;
}

export function FolderCard({ folder, onOpen, onRename, onDelete, onDropFile }: FolderCardProps) {
  const [isDragOver, setIsDragOver] = useState(false);

  return (
    <div
      onClick={onOpen}
      onDragOver={(e) => {
        if (e.dataTransfer.types.includes('text/x-file-id')) {
          e.preventDefault();
          setIsDragOver(true);
        }
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragOver(false);
        const fileId = e.dataTransfer.getData('text/x-file-id');
        if (fileId) onDropFile(fileId);
      }}
      className={`group flex cursor-pointer items-center justify-between gap-2 rounded-2xl border p-4 transition ${
        isDragOver
          ? 'border-cyan-500 bg-cyan-500/10'
          : 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-800 dark:bg-slate-900/60 dark:hover:border-slate-700'
      }`}
    >
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-500/10 text-amber-500">
          <Folder size={18} />
        </div>
        <p className="truncate text-sm font-medium text-slate-900 dark:text-white">{folder.name}</p>
      </div>
      <ItemMenu
        actions={[
          { label: 'Rename', onSelect: onRename },
          { label: 'Delete', onSelect: onDelete, danger: true },
        ]}
      />
    </div>
  );
}
