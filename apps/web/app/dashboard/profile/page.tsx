'use client';

import { useState, type FormEvent } from 'react';
import { useAuth } from '@/components/auth-provider';
import { changePassword } from '@/lib/auth';
import { ApiError } from '@/lib/api-client';
import { FormButton, FormError, FormField, FormInput, FormSuccess } from '@/components/ui/form';
import { SkeletonRows } from '@/components/ui/skeleton';

export default function ProfilePage() {
  const { user, isLoading } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);
    try {
      await changePassword(currentPassword, newPassword);
      setSuccess('Password changed successfully.');
      setCurrentPassword('');
      setNewPassword('');
    } catch (err) {
      setError(err instanceof ApiError ? String(err.detail) : 'Unable to change password.');
    } finally {
      setLoading(false);
    }
  };

  if (isLoading || !user) return <SkeletonRows count={3} />;

  const initials = `${user.first_name?.[0] ?? ''}${user.last_name?.[0] ?? ''}`.toUpperCase();

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Profile</h2>

      <div className="flex items-center gap-4 rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-cyan-500 text-xl font-semibold text-slate-950">
          {initials || '?'}
        </div>
        <div>
          <p className="text-lg font-semibold text-slate-900 dark:text-white">{user.first_name} {user.last_name}</p>
          <p className="text-sm text-slate-500 dark:text-slate-400">{user.email}</p>
          <p className="mt-1 text-xs">
            {user.is_verified ? (
              <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-emerald-600 dark:text-emerald-300">Verified</span>
            ) : (
              <span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-amber-600 dark:text-amber-300">Unverified</span>
            )}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/60">
        <h3 className="font-semibold text-slate-900 dark:text-white">Change password</h3>
        <FormError message={error} />
        <FormSuccess message={success} />

        <div>
          <FormField label="Current password" htmlFor="current-password" />
          <FormInput
            id="current-password"
            type="password"
            required
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            autoComplete="current-password"
          />
        </div>
        <div>
          <FormField label="New password" htmlFor="new-password" />
          <FormInput
            id="new-password"
            type="password"
            required
            minLength={10}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            autoComplete="new-password"
          />
        </div>

        <FormButton type="submit" loading={loading} className="w-auto px-6">
          Update password
        </FormButton>
      </form>
    </div>
  );
}
