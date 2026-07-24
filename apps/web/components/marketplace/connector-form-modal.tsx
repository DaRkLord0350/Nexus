'use client';

import { useState } from 'react';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import { Modal } from '@/components/ui/modal';
import type { MarketplaceConnectorCreateInput } from '@/lib/marketplace/connectors';

interface ConnectorFormModalProps {
  onSubmit: (data: MarketplaceConnectorCreateInput) => Promise<void>;
  onClose: () => void;
}

const CONNECTOR_TYPES = ['woocommerce', 'amazon', 'flipkart', 'shopify', 'etsy', 'ebay', 'other'];

export function ConnectorFormModal({ onSubmit, onClose }: ConnectorFormModalProps) {
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [connectorType, setConnectorType] = useState('woocommerce');
  const [storeUrl, setStoreUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [webhookSecret, setWebhookSecret] = useState('');
  const [autoSyncProducts, setAutoSyncProducts] = useState(false);
  const [autoSyncOrders, setAutoSyncOrders] = useState(false);
  const [autoSyncInventory, setAutoSyncInventory] = useState(false);
  const [autoSyncPrices, setAutoSyncPrices] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    setError(null);
    if (!name.trim() || !code.trim()) {
      setError('Name and code are required.');
      return;
    }
    setSaving(true);
    try {
      await onSubmit({
        name: name.trim(),
        code: code.trim(),
        connector_type: connectorType,
        store_url: storeUrl.trim() || undefined,
        credentials: apiKey || apiSecret ? { api_key: apiKey.trim(), api_secret: apiSecret.trim() } : undefined,
        webhook_secret: webhookSecret.trim() || undefined,
        auto_sync_products: autoSyncProducts,
        auto_sync_orders: autoSyncOrders,
        auto_sync_inventory: autoSyncInventory,
        auto_sync_prices: autoSyncPrices,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create marketplace connector.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title="New marketplace connector" onClose={onClose}>
      <div className="space-y-4">
        <div>
          <FormField label="Name" htmlFor="name" />
          <FormInput id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. My WooCommerce Store" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <FormField label="Code" htmlFor="code" />
            <FormInput id="code" value={code} onChange={(e) => setCode(e.target.value)} placeholder="e.g. woo-main" />
          </div>
          <div>
            <FormField label="Marketplace" htmlFor="connector_type" />
            <select id="connector_type" value={connectorType} onChange={(e) => setConnectorType(e.target.value)} className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
              {CONNECTOR_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
        </div>
        <div>
          <FormField label="Store URL" htmlFor="store_url" />
          <FormInput id="store_url" value={storeUrl} onChange={(e) => setStoreUrl(e.target.value)} placeholder="https://shop.example.com" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <FormField label="API key" htmlFor="api_key" />
            <FormInput id="api_key" value={apiKey} onChange={(e) => setApiKey(e.target.value)} />
          </div>
          <div>
            <FormField label="API secret" htmlFor="api_secret" />
            <FormInput id="api_secret" type="password" value={apiSecret} onChange={(e) => setApiSecret(e.target.value)} />
          </div>
        </div>
        <div>
          <FormField label="Webhook secret (optional)" htmlFor="webhook_secret" />
          <FormInput id="webhook_secret" value={webhookSecret} onChange={(e) => setWebhookSecret(e.target.value)} placeholder="Verified against the X-Webhook-Secret header" />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
            <input type="checkbox" checked={autoSyncProducts} onChange={(e) => setAutoSyncProducts(e.target.checked)} />
            Auto-sync products
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
            <input type="checkbox" checked={autoSyncOrders} onChange={(e) => setAutoSyncOrders(e.target.checked)} />
            Auto-sync orders
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
            <input type="checkbox" checked={autoSyncInventory} onChange={(e) => setAutoSyncInventory(e.target.checked)} />
            Auto-sync inventory
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
            <input type="checkbox" checked={autoSyncPrices} onChange={(e) => setAutoSyncPrices(e.target.checked)} />
            Auto-sync prices
          </label>
        </div>
        <p className="text-xs text-slate-400">
          Auto-sync settings are saved for when a scheduled sync worker is configured. Until then, use the &quot;Sync now&quot; actions on the connector detail page.
        </p>
        <FormError message={error} />
        <FormButton type="button" loading={saving} onClick={handleSubmit}>
          Create connector
        </FormButton>
      </div>
    </Modal>
  );
}
