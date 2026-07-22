'use client';

import {
  ArrowLeftRight,
  Award,
  Barcode as ScanIcon,
  Bell,
  Boxes,
  Building2,
  ClipboardCheck,
  ClipboardList,
  FolderOpen,
  FolderTree,
  PackageCheck,
  Layers,
  Layers3,
  LayoutDashboard,
  ListPlus,
  ListTree,
  Package,
  PackageSearch,
  Percent,
  QrCode,
  Radio,
  ScrollText,
  Settings,
  SlidersHorizontal,
  Tag as TagIcon,
  Ticket,
  UserCircle,
  Warehouse,
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/components/auth-provider';

interface NavItem {
  href: string;
  label: string;
  icon: typeof LayoutDashboard;
  permission?: string;
}

const NAV_ITEMS: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/dashboard/catalog/categories', label: 'Categories', icon: FolderTree, permission: 'catalog.categories.view' },
  { href: '/dashboard/catalog/brands', label: 'Brands', icon: Award, permission: 'catalog.brands.view' },
  { href: '/dashboard/catalog/attributes', label: 'Attributes', icon: ListTree, permission: 'catalog.attributes.view' },
  { href: '/dashboard/catalog/products', label: 'Products', icon: Package, permission: 'catalog.products.view' },
  { href: '/dashboard/catalog/product-types', label: 'Product Types', icon: Layers3, permission: 'catalog.products.view' },
  { href: '/dashboard/catalog/collections', label: 'Collections', icon: Layers, permission: 'catalog.collections.view' },
  { href: '/dashboard/catalog/tax', label: 'Tax', icon: Percent, permission: 'catalog.tax.manage' },
  { href: '/dashboard/catalog/coupons', label: 'Coupons', icon: Ticket, permission: 'catalog.coupons.view' },
  { href: '/dashboard/catalog/tags', label: 'Tags', icon: TagIcon, permission: 'catalog.products.view' },
  { href: '/dashboard/catalog/channels', label: 'Channels', icon: Radio, permission: 'catalog.products.view' },
  { href: '/dashboard/catalog/custom-fields', label: 'Custom Fields', icon: ListPlus, permission: 'catalog.products.view' },
  { href: '/dashboard/inventory/warehouses', label: 'Warehouses', icon: Warehouse, permission: 'inventory.warehouses.view' },
  { href: '/dashboard/inventory/stock', label: 'Inventory', icon: PackageSearch, permission: 'inventory.stock.view' },
  { href: '/dashboard/inventory/barcodes', label: 'Barcode Center', icon: QrCode, permission: 'inventory.barcodes.view' },
  { href: '/dashboard/inventory/batches', label: 'Batches', icon: Boxes, permission: 'inventory.batches.view' },
  { href: '/dashboard/inventory/serial-numbers', label: 'Serial Numbers', icon: ScanIcon, permission: 'inventory.serials.view' },
  { href: '/dashboard/inventory/purchase-orders', label: 'Purchase Orders', icon: ClipboardList, permission: 'inventory.purchase_orders.view' },
  { href: '/dashboard/inventory/goods-receipts', label: 'Goods Receipts', icon: PackageCheck, permission: 'inventory.goods_receipts.view' },
  { href: '/dashboard/inventory/transfers', label: 'Transfers', icon: ArrowLeftRight, permission: 'inventory.transfers.view' },
  { href: '/dashboard/inventory/adjustments', label: 'Stock Adjustments', icon: SlidersHorizontal, permission: 'inventory.adjustments.view' },
  { href: '/dashboard/inventory/cycle-counts', label: 'Cycle Counts', icon: ClipboardCheck, permission: 'inventory.cycle_counts.view' },
  { href: '/dashboard/files', label: 'Files', icon: FolderOpen, permission: 'files' },
  { href: '/dashboard/audit', label: 'Audit Logs', icon: ScrollText, permission: 'audit' },
  { href: '/dashboard/notifications', label: 'Notifications', icon: Bell },
  { href: '/dashboard/organization', label: 'Organization', icon: Building2 },
  { href: '/dashboard/settings', label: 'Settings', icon: Settings, permission: 'settings' },
  { href: '/dashboard/profile', label: 'Profile', icon: UserCircle },
];

export function Sidebar() {
  const pathname = usePathname();
  const { hasPermission, isLoading } = useAuth();

  const items = NAV_ITEMS.filter((item) => !item.permission || isLoading || hasPermission(item.permission));

  return (
    <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white/80 px-4 py-6 dark:border-slate-800 dark:bg-slate-900/60 lg:block">
      <nav className="space-y-1">
        {items.map((item) => {
          const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname?.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                isActive
                  ? 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-300'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800/60 dark:hover:text-white'
              }`}
            >
              <Icon size={18} />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
