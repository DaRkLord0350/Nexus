'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState, type FormEvent } from 'react';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';
import { ApiError } from '@/lib/api-client';
import { loginCustomer } from '@/lib/customer-portal/auth';

export default function CustomerLoginPage() {
  const router = useRouter();
  const [organizationId, setOrganizationId] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await loginCustomer(organizationId.trim(), email.trim(), password);
      router.push('/portal/dashboard');
    } catch (err) {
      setError(err instanceof ApiError ? String(err.detail) : 'Unable to sign in.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-950">
      <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-xl shadow-slate-200/50 dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-black/20">
        <div className="mb-6 text-center">
          <p className="text-xs uppercase tracking-[0.3em] text-cyan-600 dark:text-cyan-300">CommerceOS</p>
          <h1 className="mt-2 text-xl font-semibold text-slate-900 dark:text-white">My account</h1>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <FormError message={error} />
          <div>
            <FormField label="Organization ID" htmlFor="organization_id" />
            <FormInput id="organization_id" required value={organizationId} onChange={(e) => setOrganizationId(e.target.value)} placeholder="Provided by the store" />
          </div>
          <div>
            <FormField label="Email" htmlFor="email" />
            <FormInput id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
          </div>
          <div>
            <FormField label="Password" htmlFor="password" />
            <FormInput id="password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
          </div>
          <FormButton type="submit" loading={loading}>Sign in</FormButton>
          <p className="text-center text-sm text-slate-500 dark:text-slate-400">
            New here?{' '}
            <Link href="/portal/register" className="font-medium text-cyan-600 hover:underline dark:text-cyan-300">
              Create an account
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
