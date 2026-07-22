'use client';

import { Pencil, Radio, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { ChannelFormModal } from '@/components/catalog/channel-form-modal';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { SkeletonRows } from '@/components/ui/skeleton';
import { createChannel, deleteChannel, fetchChannels, updateChannel, type ChannelCreateInput } from '@/lib/catalog/channels';
import type { ChannelItem } from '@/lib/types';

export default function ChannelsPage() {
  const [items, setItems] = useState<ChannelItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formTarget, setFormTarget] = useState<ChannelItem | null | undefined>(undefined);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchChannels();
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load channels.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSave = async (data: ChannelCreateInput) => {
    if (formTarget) {
      await updateChannel(formTarget.id, data);
    } else {
      await createChannel(data);
    }
    await load();
  };

  const handleDelete = async (channel: ChannelItem) => {
    if (!confirm(`Delete channel "${channel.name}"?`)) return;
    await deleteChannel(channel.id);
    await load();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Channels</h2>
        <PermissionGuard permission="catalog.channels.manage">
          <button type="button" onClick={() => setFormTarget(null)} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400">
            New channel
          </button>
        </PermissionGuard>
      </div>

      {error ? <p className="text-sm text-red-600 dark:text-red-400">{error}</p> : null}

      {loading ? (
        <SkeletonRows count={4} />
      ) : items.length === 0 ? (
        <EmptyState icon={Radio} title="No channels found" description="Create a channel (e.g. Online Store, POS) to control where products are published." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {items.map((channel) => (
                <tr key={channel.id} className="bg-white dark:bg-slate-900/40">
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                    {channel.name}
                    {channel.is_default ? <span className="ml-2 text-xs text-cyan-500">default</span> : null}
                  </td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{channel.channel_type}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{channel.is_active ? 'Active' : 'Inactive'}</td>
                  <td className="px-4 py-3">
                    <PermissionGuard permission="catalog.channels.manage">
                      <div className="flex justify-end gap-2">
                        <button type="button" onClick={() => setFormTarget(channel)} className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white">
                          <Pencil size={16} />
                        </button>
                        <button type="button" onClick={() => handleDelete(channel)} className="rounded-lg p-1.5 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10">
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </PermissionGuard>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {formTarget !== undefined ? (
        <ChannelFormModal channel={formTarget} onSubmit={handleSave} onClose={() => setFormTarget(undefined)} />
      ) : null}
    </div>
  );
}
