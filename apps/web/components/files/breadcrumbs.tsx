import { ChevronRight, Home } from 'lucide-react';
import type { BreadcrumbItem } from '@/lib/types';

interface FileBreadcrumbsProps {
  items: BreadcrumbItem[];
  onNavigate: (folderId: string | null) => void;
}

export function FileBreadcrumbs({ items, onNavigate }: FileBreadcrumbsProps) {
  return (
    <nav className="flex flex-wrap items-center gap-1 text-sm text-slate-500 dark:text-slate-400">
      <button
        type="button"
        onClick={() => onNavigate(null)}
        className="flex items-center gap-1 rounded-lg px-2 py-1 font-medium text-slate-700 transition hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
      >
        <Home size={14} />
        Files
      </button>
      {items.map((item) => (
        <span key={item.id} className="flex items-center gap-1">
          <ChevronRight size={14} />
          <button
            type="button"
            onClick={() => onNavigate(item.id)}
            className="rounded-lg px-2 py-1 font-medium text-slate-700 transition hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            {item.name}
          </button>
        </span>
      ))}
    </nav>
  );
}
