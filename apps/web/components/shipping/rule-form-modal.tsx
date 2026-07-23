'use client';

import { useState } from 'react';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import { Modal } from '@/components/ui/modal';
import type { ShippingRuleCreateInput } from '@/lib/shipping/rules';
import type { ShippingRuleActionType, ShippingRuleConditionType } from '@/lib/types';

interface RuleFormModalProps {
  onSubmit: (data: ShippingRuleCreateInput) => Promise<void>;
  onClose: () => void;
}

const CONDITION_TYPES: ShippingRuleConditionType[] = ['weight_greater_than', 'weight_less_than', 'is_cod', 'destination_state', 'destination_country', 'order_value_greater_than'];
const ACTION_TYPES: ShippingRuleActionType[] = ['assign_provider', 'exclude_provider', 'prefer_warehouse'];

export function RuleFormModal({ onSubmit, onClose }: RuleFormModalProps) {
  const [name, setName] = useState('');
  const [priority, setPriority] = useState('0');
  const [conditionType, setConditionType] = useState<ShippingRuleConditionType>('weight_greater_than');
  const [conditionValue, setConditionValue] = useState('');
  const [actionType, setActionType] = useState<ShippingRuleActionType>('assign_provider');
  const [actionValue, setActionValue] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    setError(null);
    if (!name.trim() || !conditionValue.trim() || !actionValue.trim()) {
      setError('Please fill in all fields.');
      return;
    }
    setSaving(true);
    try {
      await onSubmit({ name: name.trim(), priority: Number(priority) || 0, condition_type: conditionType, condition_value: conditionValue.trim(), action_type: actionType, action_value: actionValue.trim() });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create rule.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title="New shipping rule" onClose={onClose}>
      <div className="space-y-4">
        <div>
          <FormField label="Name" htmlFor="name" />
          <FormInput id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Heavy packages via freight" />
        </div>
        <div>
          <FormField label="Priority (lower runs first)" htmlFor="priority" />
          <FormInput id="priority" type="number" value={priority} onChange={(e) => setPriority(e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <FormField label="If condition" htmlFor="condition_type" />
            <select id="condition_type" value={conditionType} onChange={(e) => setConditionType(e.target.value as ShippingRuleConditionType)} className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
              {CONDITION_TYPES.map((c) => (
                <option key={c} value={c}>{c.replace(/_/g, ' ')}</option>
              ))}
            </select>
          </div>
          <div>
            <FormField label="Value" htmlFor="condition_value" />
            <FormInput id="condition_value" value={conditionValue} onChange={(e) => setConditionValue(e.target.value)} placeholder="e.g. 5 or true or CA" />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <FormField label="Then action" htmlFor="action_type" />
            <select id="action_type" value={actionType} onChange={(e) => setActionType(e.target.value as ShippingRuleActionType)} className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950/60 dark:text-white">
              {ACTION_TYPES.map((a) => (
                <option key={a} value={a}>{a.replace(/_/g, ' ')}</option>
              ))}
            </select>
          </div>
          <div>
            <FormField label="Target ID" htmlFor="action_value" />
            <FormInput id="action_value" value={actionValue} onChange={(e) => setActionValue(e.target.value)} placeholder="provider or warehouse ID" />
          </div>
        </div>
        <FormError message={error} />
        <FormButton type="button" loading={saving} onClick={handleSubmit}>
          Create rule
        </FormButton>
      </div>
    </Modal>
  );
}
