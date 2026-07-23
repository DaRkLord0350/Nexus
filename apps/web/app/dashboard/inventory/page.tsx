'use client';

import { AlertTriangle, PackageSearch } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { DashboardCard } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';
import { SkeletonGrid } from '@/components/ui/skeleton';
import { fetchPurchaseOrders } from '@/lib/inventory/purchase-orders';
import { fetchInventory } from '@/lib/inventory/stock';
import { fetchTransfers } from '@/lib/inventory/transfers';
import { fetchWarehouses } from '@/lib/inventory/warehouses';
import type { InventoryItem } from '@/lib/types';

export default function InventoryDashboardPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [warehouseCount, setWarehouseCount] = useState(0);
  const [lowStockItems, setLowStockItems] = useState<InventoryItem[]>([]);
  const [lowStockTotal, setLowStockTotal] = useState(0);
  const [openPurchaseOrders, setOpenPurchaseOrders] = useState(0);
  const [inTransitTransfers, setInTransitTransfers] = useState(0);
  const [productNames, setProductNames] = useState<Record<string, string>>({});
  const [warehouseNames, setWarehouseNames] = useState<Record<string, string>>({});

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [warehousesData, lowStockData, sentPos, partialPos, shippedTransfers] = await Promise.all([
          fetchWarehouses({ limit: 200 }),
          fetchInventory({ lowStockOnly: true, limit: 10 }),
          fetchPurchaseOrders({ status: 'sent', limit: 1 }),
          fetchPurchaseOrders({ status: 'partially_received', limit: 1 }),
          fetchTransfers({ status: 'shipped', limit: 1 }),
        ]);
        setWarehouseCount(warehousesData.total);
        setWarehouseNames(Object.fromEntries(warehousesData.items.map((w) => [w.id, w.name])));
        setLowStockItems(lowStockData.items);
        setLowStockTotal(lowStockData.total);
        setOpenPurchaseOrders(sentPos.total + partialPos.total);
        setInTransitTransfers(shippedTransfers.total);

        try {
          const { fetchProducts } = await import('@/lib/catalog/products');
          const productsData = await fetchProducts({ limit: 200 });
          setProductNames(Object.fromEntries(productsData.items.map((p) => [p.id, p.name])));
        } catch {
          // Product name lookup is cosmetic — fall back to raw ids.
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load inventory dashboard.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (error) {
    return <EmptyState icon={AlertTriangle} title="Unable to load dashboard" description={error} />;
  }

  if (loading) {
    return <SkeletonGrid />;
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Inventory Dashboard</h2>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">A snapshot of stock health across your warehouses.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        <DashboardCard title="Warehouses" value={warehouseCount} />
        <DashboardCard title="Low Stock Items" value={lowStockTotal} subtitle={lowStockTotal > 0 ? 'Needs attention' : undefined} />
        <DashboardCard title="Open Purchase Orders" value={openPurchaseOrders} />
        <DashboardCard title="Transfers In Transit" value={inTransitTransfers} />
      </div>

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-lg shadow-slate-200/50 dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-black/10">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-500 dark:text-slate-400">Attention needed</p>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Low stock items</h3>
          </div>
          <Link href="/dashboard/inventory/stock" className="text-sm font-medium text-cyan-600 hover:text-cyan-500 dark:text-cyan-400">
            View all
          </Link>
        </div>

        {lowStockItems.length === 0 ? (
          <EmptyState icon={PackageSearch} title="No low stock items" description="Every tracked product is above its reorder point." />
        ) : (
          <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-3">Product</th>
                  <th className="px-4 py-3">Warehouse</th>
                  <th className="px-4 py-3">Available</th>
                  <th className="px-4 py-3">Reorder point</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {lowStockItems.map((item) => (
                  <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{productNames[item.product_id] ?? item.product_id}</td>
                    <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{warehouseNames[item.warehouse_id] ?? item.warehouse_id}</td>
                    <td className="px-4 py-3 font-medium text-amber-600 dark:text-amber-400">{item.quantity_available}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.reorder_point ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          { href: '/dashboard/inventory/warehouses', label: 'Warehouses' },
          { href: '/dashboard/inventory/purchase-orders', label: 'Purchase Orders' },
          { href: '/dashboard/inventory/transfers', label: 'Stock Transfers' },
          { href: '/dashboard/inventory/reorder-rules', label: 'Reorder Rules' },
        ].map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="rounded-2xl border border-slate-200 bg-white p-4 text-sm font-medium text-slate-700 transition hover:border-cyan-300 hover:text-cyan-600 dark:border-slate-800 dark:bg-slate-900/60 dark:text-slate-300 dark:hover:border-cyan-700 dark:hover:text-cyan-300"
          >
            {link.label} →
          </Link>
        ))}
      </div>
    </div>
  );
}
