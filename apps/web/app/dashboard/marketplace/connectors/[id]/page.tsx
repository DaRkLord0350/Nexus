'use client';

import { ArrowLeft, RefreshCw } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { fetchMarketplaceConnector } from '@/lib/marketplace/connectors';
import { fetchMarketplaceOrderLinks } from '@/lib/marketplace/orders';
import { fetchMarketplaceProductLinks } from '@/lib/marketplace/products';
import { fetchMarketplaceSyncLogs, syncMarketplaceInventory, syncMarketplaceOrders, syncMarketplacePrices, syncMarketplaceProducts } from '@/lib/marketplace/sync';
import { fetchMarketplaceWebhookEvents, retryMarketplaceWebhookEvents } from '@/lib/marketplace/webhooks';
import type {
  MarketplaceConnectorRead,
  MarketplaceOrderLinkRead,
  MarketplaceProductLinkRead,
  MarketplaceSyncLogRead,
  MarketplaceWebhookEventRead,
} from '@/lib/types';

const STATUS_COLOR: Record<string, string> = {
  success: 'text-emerald-600 dark:text-emerald-400',
  synced: 'text-emerald-600 dark:text-emerald-400',
  imported: 'text-emerald-600 dark:text-emerald-400',
  processed: 'text-emerald-600 dark:text-emerald-400',
  partial: 'text-amber-600 dark:text-amber-400',
  pending: 'text-slate-500 dark:text-slate-400',
  failed: 'text-red-600 dark:text-red-400',
};

function StatusBadge({ status }: { status: string }) {
  return <span className={`capitalize font-medium ${STATUS_COLOR[status] ?? 'text-slate-500 dark:text-slate-400'}`}>{status.replace(/_/g, ' ')}</span>;
}

export default function MarketplaceConnectorDetailPage() {
  const params = useParams<{ id: string }>();
  const connectorId = params.id;

  const [connector, setConnector] = useState<MarketplaceConnectorRead | null>(null);
  const [productLinks, setProductLinks] = useState<MarketplaceProductLinkRead[]>([]);
  const [orderLinks, setOrderLinks] = useState<MarketplaceOrderLinkRead[]>([]);
  const [syncLogs, setSyncLogs] = useState<MarketplaceSyncLogRead[]>([]);
  const [webhookEvents, setWebhookEvents] = useState<MarketplaceWebhookEventRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [connectorData, products, orders, logs, events] = await Promise.all([
        fetchMarketplaceConnector(connectorId),
        fetchMarketplaceProductLinks(connectorId),
        fetchMarketplaceOrderLinks(connectorId),
        fetchMarketplaceSyncLogs(connectorId),
        fetchMarketplaceWebhookEvents(connectorId),
      ]);
      setConnector(connectorData);
      setProductLinks(products.items);
      setOrderLinks(orders.items);
      setSyncLogs(logs.items);
      setWebhookEvents(events.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load this connector.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (connectorId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [connectorId]);

  const runSync = async (key: string, fn: () => Promise<unknown>) => {
    setSyncing(key);
    setError(null);
    try {
      await fn();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sync failed.');
    } finally {
      setSyncing(null);
    }
  };

  const handleRetryWebhooks = () => runSync('retry', () => retryMarketplaceWebhookEvents(connectorId));

  if (loading) return <SkeletonRows count={6} />;

  return (
    <div className="space-y-6">
      <Link href="/dashboard/marketplace/connectors" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
        <ArrowLeft size={14} /> Back to connectors
      </Link>

      <FormError message={error} />

      {!connector ? (
        <EmptyState title="Connector not found" />
      ) : (
        <>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{connector.name}</h2>
                <p className="mt-1 text-sm capitalize text-slate-500 dark:text-slate-400">
                  {connector.connector_type} · {connector.is_active ? 'Active' : 'Inactive'} · Last sync: {connector.last_sync_at ? new Date(connector.last_sync_at).toLocaleString() : 'Never'}
                </p>
              </div>
              <PermissionGuard permission="marketplace.sync.manage">
                <div className="flex flex-wrap gap-2">
                  <button type="button" disabled={syncing !== null} onClick={() => runSync('products', () => syncMarketplaceProducts(connectorId))} className="flex items-center gap-1.5 rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400 disabled:opacity-50">
                    <RefreshCw size={14} className={syncing === 'products' ? 'animate-spin' : ''} /> Sync products
                  </button>
                  <button type="button" disabled={syncing !== null} onClick={() => runSync('inventory', () => syncMarketplaceInventory(connectorId))} className="flex items-center gap-1.5 rounded-xl border border-slate-300 px-3.5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:text-slate-200">
                    <RefreshCw size={14} className={syncing === 'inventory' ? 'animate-spin' : ''} /> Sync inventory
                  </button>
                  <button type="button" disabled={syncing !== null} onClick={() => runSync('prices', () => syncMarketplacePrices(connectorId))} className="flex items-center gap-1.5 rounded-xl border border-slate-300 px-3.5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:text-slate-200">
                    <RefreshCw size={14} className={syncing === 'prices' ? 'animate-spin' : ''} /> Sync prices
                  </button>
                  <button type="button" disabled={syncing !== null} onClick={() => runSync('orders', () => syncMarketplaceOrders(connectorId))} className="flex items-center gap-1.5 rounded-xl border border-slate-300 px-3.5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:text-slate-200">
                    <RefreshCw size={14} className={syncing === 'orders' ? 'animate-spin' : ''} /> Sync orders
                  </button>
                </div>
              </PermissionGuard>
            </div>
          </div>

          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Product listings ({productLinks.length})</h3>
          {productLinks.length === 0 ? (
            <EmptyState title="No products listed yet" description="Run 'Sync products' to list your catalog on this marketplace." />
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                  <tr><th className="px-4 py-3">External ID</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Price</th><th className="px-4 py-3">Qty</th><th className="px-4 py-3">Last synced</th></tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {productLinks.map((link) => (
                    <tr key={link.id} className="bg-white dark:bg-slate-900/40">
                      <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{link.external_id ?? '—'}</td>
                      <td className="px-4 py-3"><StatusBadge status={link.sync_status} /></td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{link.last_synced_price ?? '—'}</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{link.last_synced_quantity ?? '—'}</td>
                      <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{link.last_synced_at ? new Date(link.last_synced_at).toLocaleString() : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Imported orders ({orderLinks.length})</h3>
          {orderLinks.length === 0 ? (
            <EmptyState title="No orders imported yet" description="Marketplace orders arrive via webhook, or run 'Sync orders' to pull manually." />
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                  <tr><th className="px-4 py-3">External order #</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Order</th><th className="px-4 py-3">Imported</th></tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {orderLinks.map((link) => (
                    <tr key={link.id} className="bg-white dark:bg-slate-900/40">
                      <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{link.external_order_number ?? link.external_order_id}</td>
                      <td className="px-4 py-3"><StatusBadge status={link.status} /></td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                        {link.order_id ? <Link href={`/dashboard/orders/${link.order_id}`} className="text-cyan-600 hover:text-cyan-500 dark:text-cyan-400">View order</Link> : (link.last_error ?? '—')}
                      </td>
                      <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{link.imported_at ? new Date(link.imported_at).toLocaleString() : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Webhook events ({webhookEvents.length})</h3>
            <PermissionGuard permission="marketplace.sync.manage">
              <button type="button" disabled={syncing !== null} onClick={handleRetryWebhooks} className="rounded-xl border border-slate-300 px-3 py-1.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:text-slate-200">
                Retry due events
              </button>
            </PermissionGuard>
          </div>
          {webhookEvents.length === 0 ? (
            <EmptyState title="No webhook events received yet" description="Point this marketplace's webhooks at /api/v1/marketplace/webhooks/." />
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                  <tr><th className="px-4 py-3">Event</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Retries</th><th className="px-4 py-3">Received</th></tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {webhookEvents.map((event) => (
                    <tr key={event.id} className="bg-white dark:bg-slate-900/40">
                      <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{event.event_type}</td>
                      <td className="px-4 py-3"><StatusBadge status={event.status} /></td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{event.retry_count}</td>
                      <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{new Date(event.received_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Sync history ({syncLogs.length})</h3>
          {syncLogs.length === 0 ? (
            <EmptyState title="No sync runs yet" description="Trigger a sync above to see its result here." />
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                  <tr><th className="px-4 py-3">Type</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Processed</th><th className="px-4 py-3">Succeeded</th><th className="px-4 py-3">Failed</th><th className="px-4 py-3">Started</th></tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {syncLogs.map((log) => (
                    <tr key={log.id} className="bg-white dark:bg-slate-900/40">
                      <td className="px-4 py-3 font-medium capitalize text-slate-900 dark:text-white">{log.sync_type}</td>
                      <td className="px-4 py-3"><StatusBadge status={log.status} /></td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{log.items_processed}</td>
                      <td className="px-4 py-3 text-emerald-600 dark:text-emerald-400">{log.items_succeeded}</td>
                      <td className="px-4 py-3 text-red-600 dark:text-red-400">{log.items_failed}</td>
                      <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{new Date(log.started_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
