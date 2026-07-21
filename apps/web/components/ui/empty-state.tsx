import type { LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-slate-300 bg-slate-50/50 p-10 text-center dark:border-slate-700 dark:bg-slate-900/40">
      {Icon ? (
        <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-slate-200 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
          <Icon size={20} />
        </div>
      ) : null}
      <p className="text-base font-semibold text-slate-900 dark:text-white">{title}</p>
      {description ? <p className="mt-1 max-w-sm text-sm text-slate-500 dark:text-slate-400">{description}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
