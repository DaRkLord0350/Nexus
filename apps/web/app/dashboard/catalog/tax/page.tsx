'use client';

import { Pencil, Percent, Plus, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { TaxClassFormModal } from '@/components/catalog/tax-class-form-modal';
import { TaxRateFormModal } from '@/components/catalog/tax-rate-form-modal';
import { PermissionGuard } from '@/components/permission-guard';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import {
  createTaxClass,
  createTaxRate,
  deleteTaxClass,
  deleteTaxRate,
  fetchTaxClasses,
  fetchTaxRates,
  updateTaxClass,
  updateTaxRate,
  type TaxClassCreateInput,
  type TaxRateCreateInput,
} from '@/lib/catalog/tax';
import type { TaxClassItem, TaxRateItem } from '@/lib/types';

export default function TaxPage() {
  const [items, setItems] = useState<TaxClassItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [rates, setRates] = useState<TaxRateItem[]>([]);
  const [ratesLoading, setRatesLoading] = useState(false);

  const [classFormTarget, setClassFormTarget] = useState<TaxClassItem | null | undefined>(undefined);
  const [rateFormTarget, setRateFormTarget] = useState<TaxRateItem | null | undefined>(undefined);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchTaxClasses();
      setItems(data.items);
      if (!selectedId && data.items.length > 0) setSelectedId(data.items[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load tax classes.');
    } finally {
      setLoading(false);
    }
  };

  const loadRates = async (taxClassId: string) => {
    setRatesLoading(true);
    try {
      setRates(await fetchTaxRates(taxClassId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load tax rates.');
    } finally {
      setRatesLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (selectedId) loadRates(selectedId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  const handleSaveClass = async (data: TaxClassCreateInput) => {
    if (classFormTarget) {
      await updateTaxClass(classFormTarget.id, data);
    } else {
      const created = await createTaxClass(data);
      setSelectedId(created.id);
    }
    await load();
  };

  const handleDeleteClass = async (taxClass: TaxClassItem) => {
    if (!confirm(`Delete "${taxClass.name}" and all its rates?`)) return;
    await deleteTaxClass(taxClass.id);
    if (selectedId === taxClass.id) setSelectedId(null);
    await load();
  };

  const handleSaveRate = async (data: TaxRateCreateInput) => {
    if (!selectedId) return;
    if (rateFormTarget) {
      await updateTaxRate(selectedId, rateFormTarget.id, data);
    } else {
      await createTaxRate(selectedId, data);
    }
    await loadRates(selectedId);
  };

  const handleDeleteRate = async (rate: TaxRateItem) => {
    if (!selectedId || !confirm(`Delete this ${rate.country} rate?`)) return;
    await deleteTaxRate(selectedId, rate.id);
    await loadRates(selectedId);
  };

  const selectedClass = items.find((i) => i.id === selectedId) ?? null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Tax</h2>
        <PermissionGuard permission="catalog.tax.manage">
          <button type="button" onClick={() => setClassFormTarget(null)} className="flex items-center gap-2 rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400">
            <Plus size={16} /> New tax class
          </button>
        </PermissionGuard>
      </div>

      <FormError message={error} />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
        <div className="space-y-3">
          {loading ? (
            <SkeletonRows count={4} />
          ) : items.length === 0 ? (
            <EmptyState icon={Percent} title="No tax classes found" description="Create a tax class (e.g. Standard GST) to start configuring rates." />
          ) : (
            <div className="divide-y divide-slate-100 rounded-2xl border border-slate-200 dark:divide-slate-800 dark:border-slate-800">
              {items.map((taxClass) => (
                <button
                  key={taxClass.id}
                  type="button"
                  onClick={() => setSelectedId(taxClass.id)}
                  className={`flex w-full items-center justify-between px-4 py-3 text-left text-sm transition ${
                    selectedId === taxClass.id
                      ? 'bg-cyan-500/10 text-cyan-700 dark:text-cyan-300'
                      : 'bg-white text-slate-700 hover:bg-slate-50 dark:bg-slate-900/40 dark:text-slate-200 dark:hover:bg-slate-800/60'
                  }`}
                >
                  <span>
                    <span className="font-medium">{taxClass.name}</span>
                    {taxClass.is_default ? <span className="ml-2 text-xs text-cyan-500">default</span> : null}
                    {!taxClass.is_active ? <span className="ml-2 text-xs text-amber-500">inactive</span> : null}
                  </span>
                  <PermissionGuard permission="catalog.tax.manage">
                    <span className="flex gap-1.5">
                      <span role="button" tabIndex={0} onClick={(e) => { e.stopPropagation(); setClassFormTarget(taxClass); }} className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800 dark:hover:text-white">
                        <Pencil size={14} />
                      </span>
                      <span role="button" tabIndex={0} onClick={(e) => { e.stopPropagation(); handleDeleteClass(taxClass); }} className="rounded-lg p-1 text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10">
                        <Trash2 size={14} />
                      </span>
                    </span>
                  </PermissionGuard>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-slate-200 p-4 dark:border-slate-800">
          {!selectedClass ? (
            <EmptyState title="Select a tax class" description="Choose a tax class on the left to manage its rates." />
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-slate-900 dark:text-white">{selectedClass.name} rates</h3>
                <PermissionGuard permission="catalog.tax.manage">
                  <button type="button" onClick={() => setRateFormTarget(null)} className="rounded-xl bg-cyan-500 px-3 py-1.5 text-xs font-semibold text-slate-950 transition hover:bg-cyan-400">
                    Add rate
                  </button>
                </PermissionGuard>
              </div>

              {ratesLoading ? (
                <SkeletonRows count={3} />
              ) : rates.length === 0 ? (
                <EmptyState title="No rates yet" description="Add a country/state rate for this tax class." />
              ) : (
                <div className="space-y-2">
                  {rates.map((rate) => (
                    <div key={rate.id} className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-950/60">
                      <span className="text-slate-800 dark:text-slate-100">
                        {rate.country}{rate.state ? ` / ${rate.state}` : ''} · {rate.rate}% ({rate.tax_type}) {rate.is_inclusive ? '· inclusive' : ''}
                      </span>
                      <PermissionGuard permission="catalog.tax.manage">
                        <div className="flex gap-2">
                          <button type="button" onClick={() => setRateFormTarget(rate)} className="rounded-lg p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white">
                            <Pencil size={14} />
                          </button>
                          <button type="button" onClick={() => handleDeleteRate(rate)} className="rounded-lg p-1 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10">
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </PermissionGuard>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {classFormTarget !== undefined ? (
        <TaxClassFormModal taxClass={classFormTarget} onSubmit={handleSaveClass} onClose={() => setClassFormTarget(undefined)} />
      ) : null}
      {rateFormTarget !== undefined && selectedId ? (
        <TaxRateFormModal rate={rateFormTarget} onSubmit={handleSaveRate} onClose={() => setRateFormTarget(undefined)} />
      ) : null}
    </div>
  );
}
