'use client';

import { Trash2, Workflow } from 'lucide-react';
import { useEffect, useState } from 'react';
import { PermissionGuard } from '@/components/permission-guard';
import { RuleFormModal } from '@/components/shipping/rule-form-modal';
import { EmptyState } from '@/components/ui/empty-state';
import { FormError } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { createShippingRule, deleteShippingRule, fetchShippingRules, updateShippingRule, type ShippingRuleCreateInput } from '@/lib/shipping/rules';
import type { ShippingRuleRead } from '@/lib/types';

export default function ShippingRulesPage() {
  const [items, setItems] = useState<ShippingRuleRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchShippingRules();
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load shipping rules.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSave = async (data: ShippingRuleCreateInput) => {
    await createShippingRule(data);
    await load();
  };

  const handleToggleActive = async (rule: ShippingRuleRead) => {
    try {
      await updateShippingRule(rule.id, { is_active: !rule.is_active });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update rule.');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this rule?')) return;
    try {
      await deleteShippingRule(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete rule.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Shipping Rules</h2>
        <PermissionGuard permission="shipping.rules.manage">
          <button type="button" onClick={() => setShowForm(true)} className="rounded-xl bg-cyan-500 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400">
            New rule
          </button>
        </PermissionGuard>
      </div>

      <FormError message={error} />

      {loading ? (
        <SkeletonRows count={4} />
      ) : items.length === 0 ? (
        <EmptyState icon={Workflow} title="No shipping rules configured" description="Automate courier and warehouse selection with conditional rules." />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900/60 dark:text-slate-400">
              <tr><th className="px-4 py-3">Name</th><th className="px-4 py-3">If</th><th className="px-4 py-3">Then</th><th className="px-4 py-3">Priority</th><th className="px-4 py-3">Status</th><th className="px-4 py-3 text-right">Actions</th></tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {items.map((item) => (
                <tr key={item.id} className="bg-white dark:bg-slate-900/40">
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{item.name}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.condition_type.replace(/_/g, ' ')} {item.condition_value}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{item.action_type.replace(/_/g, ' ')}</td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{item.priority}</td>
                  <td className="px-4 py-3">
                    <button type="button" onClick={() => handleToggleActive(item)} className={item.is_active ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400'}>
                      {item.is_active ? 'Active' : 'Inactive'}
                    </button>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <PermissionGuard permission="shipping.rules.manage">
                      <button type="button" onClick={() => handleDelete(item.id)} className="rounded-lg p-1.5 text-red-500 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10">
                        <Trash2 size={16} />
                      </button>
                    </PermissionGuard>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showForm ? <RuleFormModal onSubmit={handleSave} onClose={() => setShowForm(false)} /> : null}
    </div>
  );
}
