'use client';

import { Download, ScrollText } from 'lucide-react';
import { useEffect, useState } from 'react';
import { AuditDetailsDrawer } from '@/components/audit/audit-details-drawer';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { downloadAuditExport, fetchAuditLogs, type AuditFilters } from '@/lib/audit';
import type { AuditLogItem } from '@/lib/types';

const MODULE_OPTIONS = ['auth', 'organizations', 'rbac', 'files', 'notifications', 'audit'];
const ACTION_OPTIONS = [
  'create', 'update', 'delete', 'login', 'logout', 'password_change',
  'role_assignment', 'role_removal', 'invitation', 'upload', 'download', 'export', 'settings_change',
];
const PAGE_SIZE = 25;

export default function AuditPage() {
  const [items, setItems] = useState<AuditLogItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [selected, setSelected] = useState<AuditLogItem | null>(null);

  const [module, setModule] = useState('');
  const [action, setAction] = useState('');
  const [entity, setEntity] = useState('');
  const [q, setQ] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const currentFilters = (): AuditFilters => ({
    module: module || undefined,
    action: action || undefined,
    entity: entity || undefined,
    q: q || undefined,
    dateFrom: dateFrom ? new Date(dateFrom).toISOString() : undefined,
    dateTo: dateTo ? new Date(dateTo).toISOString() : undefined,
    limit: PAGE_SIZE,
    offset,
  });

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAuditLogs(currentFilters());
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load audit logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offset]);

  const applyFilters = () => {
    setOffset(0);
    load();
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      await downloadAuditExport(currentFilters());
    } catch {
      setError('Unable to export audit logs.');
    } finally {
      setExporting(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Audit Logs</h2>
        <button
          type="button"
          onClick={handleExport}
          disabled={exporting}
          className="flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          <Download size={16} />
          {exporting ? 'Exporting…' : 'Export CSV'}
        </button>
      </div>

      <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/60 sm:grid-cols-2 lg:grid-cols-6">
        <select
          value={module}
          onChange={(e) => setModule(e.target.value)}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
        >
          <option value="">All modules</option>
          {MODULE_OPTIONS.map((option) => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>

        <select
          value={action}
          onChange={(e) => setAction(e.target.value)}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
        >
          <option value="">All actions</option>
          {ACTION_OPTIONS.map((option) => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>

        <input
          placeholder="Entity (e.g. File)"
          value={entity}
          onChange={(e) => setEntity(e.target.value)}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white dark:placeholder:text-slate-500"
        />

        <input
          placeholder="Search…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white dark:placeholder:text-slate-500"
        />

        <input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
        />

        <input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
        />

        <button
          type="button"
          onClick={applyFilters}
          className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 lg:col-span-6"
        >
          Apply filters
        </button>
      </div>

      <FormError message={error} />

      {loading ? (
        <SkeletonRows count={6} />
      ) : items.length === 0 ? (
        <EmptyState icon={ScrollText} title="No audit activity found" description="Try adjusting your filters." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">Timestamp</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Module</th>
                <th className="px-4 py-3">Entity</th>
                <th className="px-4 py-3">User</th>
                <th className="px-4 py-3">IP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {items.map((item) => (
                <tr
                  key={item.id}
                  onClick={() => setSelected(item)}
                  className="cursor-pointer bg-white transition hover:bg-slate-50 dark:bg-slate-900/40 dark:hover:bg-slate-800/60"
                >
                  <td className="whitespace-nowrap px-4 py-3 text-slate-500 dark:text-slate-400">
                    {new Date(item.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{item.action}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.module}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.entity ?? '—'}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.user_id ?? 'system'}</td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{item.ip_address ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {total > 0 ? (
        <div className="flex items-center justify-between text-sm text-slate-500 dark:text-slate-400">
          <span>
            Page {currentPage} of {totalPages} ({total} total)
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
              className="rounded-lg border border-slate-300 px-3 py-1.5 font-medium text-slate-700 disabled:opacity-40 dark:border-slate-700 dark:text-slate-200"
            >
              Previous
            </button>
            <button
              type="button"
              disabled={offset + PAGE_SIZE >= total}
              onClick={() => setOffset(offset + PAGE_SIZE)}
              className="rounded-lg border border-slate-300 px-3 py-1.5 font-medium text-slate-700 disabled:opacity-40 dark:border-slate-700 dark:text-slate-200"
            >
              Next
            </button>
          </div>
        </div>
      ) : null}

      {selected ? <AuditDetailsDrawer log={selected} onClose={() => setSelected(null)} /> : null}
    </div>
  );
}
