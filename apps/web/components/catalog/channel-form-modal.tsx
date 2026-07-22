'use client';

import { useState, type FormEvent } from 'react';
import { Modal } from '@/components/ui/modal';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import type { ChannelCreateInput } from '@/lib/catalog/channels';
import type { ChannelItem, ChannelType } from '@/lib/types';

interface ChannelFormModalProps {
  channel?: ChannelItem | null;
  onSubmit: (data: ChannelCreateInput) => Promise<void>;
  onClose: () => void;
}

export function ChannelFormModal({ channel, onSubmit, onClose }: ChannelFormModalProps) {
  const [name, setName] = useState(channel?.name ?? '');
  const [channelType, setChannelType] = useState(channel?.channel_type ?? 'online_store');
  const [isActive, setIsActive] = useState(channel?.is_active ?? true);
  const [isDefault, setIsDefault] = useState(channel?.is_default ?? false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await onSubmit({ name: name.trim(), channel_type: channelType, is_active: isActive, is_default: isDefault });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save channel.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title={channel ? 'Edit channel' : 'New channel'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormError message={error} />
        <div>
          <FormField label="Name" htmlFor="ch-name" />
          <FormInput id="ch-name" autoFocus value={name} onChange={(e) => setName(e.target.value)} required placeholder="e.g. Online Store" />
        </div>
        <div>
          <FormField label="Type" htmlFor="ch-type" />
          <select id="ch-type" value={channelType} onChange={(e) => setChannelType(e.target.value as ChannelType)} className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
            <option value="online_store">Online Store</option>
            <option value="pos">POS</option>
            <option value="mobile_app">Mobile App</option>
            <option value="marketplace">Marketplace</option>
            <option value="social">Social</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div className="flex gap-6">
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
            Active
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input type="checkbox" checked={isDefault} onChange={(e) => setIsDefault(e.target.checked)} />
            Default channel
          </label>
        </div>
        <FormButton type="submit" loading={loading}>
          {channel ? 'Save changes' : 'Create channel'}
        </FormButton>
      </form>
    </Modal>
  );
}
