'use client';

import { X } from 'lucide-react';
import type { AuditLogItem } from '@/lib/types';

export function AuditDetailsDrawer({ log, onClose }: { log: AuditLogItem; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/50" onClick={onClose}>
      <div
        onClick={(e) => e.stopPropagation()}
        className="h-full w-full max-w-md overflow-y-auto border-l border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900"
      >
        <div className="mb-6 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Audit log details</h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
          >
            <X size={18} />
          </button>
        </div>

        <dl className="space-y-4 text-sm">
          <Row label="Action" value={log.action} />
          <Row label="Module" value={log.module} />
          <Row label="Entity" value={log.entity ?? '—'} />
          <Row label="Entity ID" value={log.entity_id ?? '—'} />
          <Row label="User ID" value={log.user_id ?? 'system'} />
          <Row label="IP address" value={log.ip_address ?? '—'} />
          <Row label="Browser / agent" value={log.user_agent ?? '—'} />
          <Row label="Request ID" value={log.request_id ?? '—'} />
          <Row label="Timestamp" value={new Date(log.created_at).toLocaleString()} />

          {log.before ? (
            <div>
              <dt className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">Before</dt>
              <dd>
                <pre className="overflow-x-auto rounded-xl bg-slate-100 p-3 text-xs text-slate-700 dark:bg-slate-950 dark:text-slate-300">
                  {JSON.stringify(log.before, null, 2)}
                </pre>
              </dd>
            </div>
          ) : null}

          {log.after ? (
            <div>
              <dt className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">After</dt>
              <dd>
                <pre className="overflow-x-auto rounded-xl bg-slate-100 p-3 text-xs text-slate-700 dark:bg-slate-950 dark:text-slate-300">
                  {JSON.stringify(log.after, null, 2)}
                </pre>
              </dd>
            </div>
          ) : null}
        </dl>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-slate-100 pb-2 dark:border-slate-800">
      <dt className="text-slate-500 dark:text-slate-400">{label}</dt>
      <dd className="truncate text-right font-medium text-slate-900 dark:text-white">{value}</dd>
    </div>
  );
}
