'use client';

import { useEffect, useState } from 'react';
import { FormButton, FormError, FormField, FormInput, FormSuccess } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';
import { fetchMyProfileDetails, updateMyProfileDetails } from '@/lib/customer-portal/profile';
import type { CustomerItem } from '@/lib/types';

export default function PortalProfilePage() {
  const [profile, setProfile] = useState<CustomerItem | null>(null);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phone, setPhone] = useState('');
  const [acceptsMarketing, setAcceptsMarketing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await fetchMyProfileDetails();
        setProfile(data);
        setFirstName(data.first_name);
        setLastName(data.last_name);
        setPhone(data.phone ?? '');
        setAcceptsMarketing(data.accepts_marketing);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load your profile.');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const updated = await updateMyProfileDetails({ first_name: firstName, last_name: lastName, phone: phone || undefined, accepts_marketing: acceptsMarketing });
      setProfile(updated);
      setSuccess('Profile updated.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update profile.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <SkeletonRows count={4} />;

  return (
    <div className="max-w-lg space-y-6">
      <h2 className="text-xl font-semibold text-slate-900 dark:text-white">My profile</h2>
      <FormError message={error} />
      <FormSuccess message={success} />

      <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
        <div>
          <FormField label="Email" htmlFor="email" />
          <FormInput id="email" value={profile?.email ?? ''} disabled className="opacity-60" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <FormField label="First name" htmlFor="first_name" />
            <FormInput id="first_name" value={firstName} onChange={(e) => setFirstName(e.target.value)} />
          </div>
          <div>
            <FormField label="Last name" htmlFor="last_name" />
            <FormInput id="last_name" value={lastName} onChange={(e) => setLastName(e.target.value)} />
          </div>
        </div>
        <div>
          <FormField label="Phone" htmlFor="phone" />
          <FormInput id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
          <input type="checkbox" checked={acceptsMarketing} onChange={(e) => setAcceptsMarketing(e.target.checked)} />
          Send me marketing emails
        </label>
        <FormButton type="button" loading={saving} onClick={handleSave}>Save changes</FormButton>
      </div>
    </div>
  );
}
