'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState, type FormEvent } from 'react';
import { ApiError } from '@/lib/api-client';
import { login } from '@/lib/auth';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof ApiError ? String(err.detail) : 'Unable to sign in.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Sign in</h2>
      <FormError message={error} />

      <div>
        <FormField label="Email" htmlFor="email" />
        <FormInput id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
      </div>

      <div>
        <div className="flex items-center justify-between">
          <FormField label="Password" htmlFor="password" />
          <Link href="/forgot-password" className="text-xs text-cyan-600 hover:underline dark:text-cyan-300">
            Forgot password?
          </Link>
        </div>
        <FormInput id="password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
      </div>

      <FormButton type="submit" loading={loading}>
        Sign in
      </FormButton>

      <p className="text-center text-sm text-slate-500 dark:text-slate-400">
        Don&apos;t have an account?{' '}
        <Link href="/signup" className="font-medium text-cyan-600 hover:underline dark:text-cyan-300">
          Create one
        </Link>
      </p>
    </form>
  );
}
