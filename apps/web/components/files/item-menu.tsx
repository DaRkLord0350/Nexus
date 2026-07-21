'use client';

import { MoreVertical } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

export interface ItemMenuAction {
  label: string;
  onSelect: () => void;
  danger?: boolean;
}

export function ItemMenu({ actions }: { actions: ItemMenuAction[] }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          setOpen((v) => !v);
        }}
        aria-label="Item actions"
        className="rounded-lg p-1.5 text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
      >
        <MoreVertical size={16} />
      </button>
      {open ? (
        <div className="absolute right-0 z-20 mt-1 w-40 rounded-xl border border-slate-200 bg-white p-1 shadow-xl dark:border-slate-800 dark:bg-slate-900">
          {actions.map((action) => (
            <button
              key={action.label}
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setOpen(false);
                action.onSelect();
              }}
              className={`block w-full rounded-lg px-3 py-1.5 text-left text-sm transition hover:bg-slate-100 dark:hover:bg-slate-800 ${
                action.danger ? 'text-red-600 dark:text-red-400' : 'text-slate-700 dark:text-slate-200'
              }`}
            >
              {action.label}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
