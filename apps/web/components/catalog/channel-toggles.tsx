'use client';

import { useEffect, useState } from 'react';
import { PermissionGuard } from '@/components/permission-guard';
import { fetchChannels } from '@/lib/catalog/channels';
import { setProductChannels } from '@/lib/catalog/channels';
import type { ChannelItem, ProductChannelItem } from '@/lib/types';

interface ChannelTogglesProps {
  productId: string;
  assigned: ProductChannelItem[];
  onChange: () => Promise<void> | void;
}

export function ChannelToggles({ productId, assigned, onChange }: ChannelTogglesProps) {
  const [allChannels, setAllChannels] = useState<ChannelItem[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchChannels(true).then((data) => setAllChannels(data.items)).catch(() => setAllChannels([]));
  }, []);

  const assignedIds = new Set(assigned.map((a) => a.channel_id));

  const toggle = async (channelId: string) => {
    setSaving(true);
    try {
      const nextIds = assignedIds.has(channelId)
        ? Array.from(assignedIds).filter((id) => id !== channelId)
        : [...Array.from(assignedIds), channelId];
      await setProductChannels(productId, nextIds);
      await onChange();
    } finally {
      setSaving(false);
    }
  };

  if (allChannels.length === 0) return null;

  return (
    <div className="space-y-2">
      <h3 className="font-semibold text-slate-900 dark:text-white">Channels</h3>
      <div className="flex flex-wrap gap-2">
        {allChannels.map((channel) => {
          const isOn = assignedIds.has(channel.id);
          return (
            <PermissionGuard key={channel.id} permission="catalog.channels.manage" fallback={
              <span className={`rounded-full px-3 py-1.5 text-xs font-medium ${isOn ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-300' : 'bg-slate-200 text-slate-600 dark:bg-slate-800 dark:text-slate-300'}`}>
                {channel.name}
              </span>
            }>
              <button
                type="button"
                disabled={saving}
                onClick={() => toggle(channel.id)}
                className={`rounded-full px-3 py-1.5 text-xs font-medium transition disabled:opacity-50 ${
                  isOn
                    ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-300'
                    : 'bg-slate-200 text-slate-600 hover:bg-slate-300 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700'
                }`}
              >
                {channel.name}
              </button>
            </PermissionGuard>
          );
        })}
      </div>
    </div>
  );
}
