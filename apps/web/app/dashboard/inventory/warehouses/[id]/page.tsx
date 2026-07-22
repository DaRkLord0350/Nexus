'use client';

import { ArrowLeft, Pencil, Plus, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { WarehouseBinFormModal } from '@/components/inventory/warehouse-bin-form-modal';
import { WarehouseZoneFormModal } from '@/components/inventory/warehouse-zone-form-modal';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import {
  createBin,
  createZone,
  deleteBin,
  deleteZone,
  fetchBins,
  fetchWarehouse,
  fetchZones,
  updateBin,
  updateZone,
  type WarehouseBinCreateInput,
  type WarehouseZoneCreateInput,
} from '@/lib/inventory/warehouses';
import type { WarehouseBinItem, WarehouseItem, WarehouseZoneItem } from '@/lib/types';

type Tab = 'zones' | 'bins';

export default function WarehouseDetailPage() {
  const params = useParams<{ id: string }>();
  const warehouseId = params.id;

  const [warehouse, setWarehouse] = useState<WarehouseItem | null>(null);
  const [zones, setZones] = useState<WarehouseZoneItem[]>([]);
  const [bins, setBins] = useState<WarehouseBinItem[]>([]);
  const [tab, setTab] = useState<Tab>('zones');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [zoneFilter, setZoneFilter] = useState('');
  const [zoneFormTarget, setZoneFormTarget] = useState<WarehouseZoneItem | null | undefined>(undefined);
  const [binFormTarget, setBinFormTarget] = useState<WarehouseBinItem | null | undefined>(undefined);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [warehouseData, zonesData, binsData] = await Promise.all([
        fetchWarehouse(warehouseId),
        fetchZones(warehouseId),
        fetchBins(warehouseId),
      ]);
      setWarehouse(warehouseData);
      setZones(zonesData.items);
      setBins(binsData.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load warehouse.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (warehouseId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [warehouseId]);

  const handleSaveZone = async (data: WarehouseZoneCreateInput) => {
    if (zoneFormTarget) {
      await updateZone(warehouseId, zoneFormTarget.id, data);
    } else {
      await createZone(warehouseId, data);
    }
    await load();
  };

  const handleDeleteZone = async (zone: WarehouseZoneItem) => {
    if (!confirm(`Delete zone "${zone.name}"?`)) return;
    try {
      await deleteZone(warehouseId, zone.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete zone.');
    }
  };

  const handleSaveBin = async (data: WarehouseBinCreateInput) => {
    if (binFormTarget) {
      await updateBin(warehouseId, binFormTarget.id, data);
    } else {
      await createBin(warehouseId, data);
    }
    await load();
  };

  const handleDeleteBin = async (bin: WarehouseBinItem) => {
    if (!confirm(`Delete bin "${bin.code}"?`)) return;
    try {
      await deleteBin(warehouseId, bin.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete bin.');
    }
  };

  const zoneName = (zoneId?: string | null) => zones.find((z) => z.id === zoneId)?.name ?? '—';
  const filteredBins = zoneFilter ? bins.filter((b) => b.zone_id === zoneFilter) : bins;

  if (loading) return <SkeletonRows count={6} />;

  return (
    <div className="space-y-6">
      <Link href="/dashboard/inventory/warehouses" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white">
        <ArrowLeft size={14} /> Back to warehouses
      </Link>

      <FormError message={error} />

      {!warehouse ? (
        <EmptyState title="Warehouse not found" />
      ) : (
        <>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{warehouse.name}</h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {warehouse.code} · {warehouse.warehouse_type.replace('_', ' ')} · {warehouse.is_active ? 'Active' : 'Inactive'}
            </p>
          </div>

          <div className="flex gap-2 border-b border-slate-200 dark:border-slate-800">
            {(['zones', 'bins'] as Tab[]).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTab(t)}
                className={`px-4 py-2 text-sm font-medium capitalize transition ${
                  tab === t
                    ? 'border-b-2 border-cyan-500 text-cyan-600 dark:text-cyan-300'
                    : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'
                }`}
              >
                {t === 'bins' ? 'Bin locations' : 'Zones'}
              </button>
            ))}
          </div>

          {tab === 'zones' ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Zones ({zones.length})</h3>
                <PermissionGuard permission="inventory.warehouses.manage">
                  <button
                    type="button"
                    onClick={() => setZoneFormTarget(null)}
                    className="flex items-center gap-1.5 rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400"
                  >
                    <Plus size={14} /> New zone
                  </button>
                </PermissionGuard>
              </div>

              {zones.length === 0 ? (
                <EmptyState title="No zones yet" description="Zones organize a warehouse into receiving, storage, picking, packing, returns, and damaged areas." />
              ) : (
                <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                      <tr>
                        <th className="px-4 py-3">Name</th>
                        <th className="px-4 py-3">Code</th>
                        <th className="px-4 py-3">Type</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {zones.map((zone) => (
                        <tr key={zone.id} className="bg-white dark:bg-slate-900/40">
                          <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{zone.name}</td>
                          <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{zone.code}</td>
                          <td className="px-4 py-3 text-slate-600 dark:text-slate-300 capitalize">{zone.zone_type}</td>
                          <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{zone.is_active ? 'Active' : 'Inactive'}</td>
                          <td className="px-4 py-3">
                            <PermissionGuard permission="inventory.warehouses.manage">
                              <div className="flex justify-end gap-2">
                                <button type="button" onClick={() => setZoneFormTarget(zone)} className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white">
                                  <Pencil size={16} />
                                </button>
                                <button type="button" onClick={() => handleDeleteZone(zone)} className="rounded-lg p-1.5 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10">
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
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-3">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Bin locations ({filteredBins.length})</h3>
                <div className="flex items-center gap-2">
                  <select
                    value={zoneFilter}
                    onChange={(e) => setZoneFilter(e.target.value)}
                    className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white"
                  >
                    <option value="">All zones</option>
                    {zones.map((zone) => (
                      <option key={zone.id} value={zone.id}>{zone.name}</option>
                    ))}
                  </select>
                  <PermissionGuard permission="inventory.warehouses.manage">
                    <button
                      type="button"
                      onClick={() => setBinFormTarget(null)}
                      className="flex items-center gap-1.5 rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-400"
                    >
                      <Plus size={14} /> New bin
                    </button>
                  </PermissionGuard>
                </div>
              </div>

              {filteredBins.length === 0 ? (
                <EmptyState title="No bin locations yet" description="Bins are the smallest pick/putaway location, e.g. A-01-01." />
              ) : (
                <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
                      <tr>
                        <th className="px-4 py-3">Code</th>
                        <th className="px-4 py-3">Zone</th>
                        <th className="px-4 py-3">Aisle/Rack/Shelf</th>
                        <th className="px-4 py-3">Capacity</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {filteredBins.map((bin) => (
                        <tr key={bin.id} className="bg-white dark:bg-slate-900/40">
                          <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{bin.code}</td>
                          <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{zoneName(bin.zone_id)}</td>
                          <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                            {[bin.aisle, bin.rack, bin.shelf].filter(Boolean).join(' / ') || '—'}
                          </td>
                          <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{bin.capacity ?? '—'}</td>
                          <td className="px-4 py-3 text-slate-600 dark:text-slate-300 capitalize">{bin.status}</td>
                          <td className="px-4 py-3">
                            <PermissionGuard permission="inventory.warehouses.manage">
                              <div className="flex justify-end gap-2">
                                <button type="button" onClick={() => setBinFormTarget(bin)} className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white">
                                  <Pencil size={16} />
                                </button>
                                <button type="button" onClick={() => handleDeleteBin(bin)} className="rounded-lg p-1.5 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10">
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
            </div>
          )}
        </>
      )}

      {zoneFormTarget !== undefined ? (
        <WarehouseZoneFormModal zone={zoneFormTarget} onSubmit={handleSaveZone} onClose={() => setZoneFormTarget(undefined)} />
      ) : null}

      {binFormTarget !== undefined ? (
        <WarehouseBinFormModal bin={binFormTarget} zones={zones} onSubmit={handleSaveBin} onClose={() => setBinFormTarget(undefined)} />
      ) : null}
    </div>
  );
}
