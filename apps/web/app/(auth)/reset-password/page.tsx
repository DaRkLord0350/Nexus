'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense, useState, type FormEvent } from 'react';
import { ApiError } from '@/lib/api-client';
import { resetPassword } from '@/lib/auth';
import { FormButton, FormError, FormField, FormInput, FormSuccess } from '@/components/ui/form';

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token') ?? '';
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await resetPassword(token, password);
      setSuccess('Your password has been reset. You can now sign in.');
    } catch (err) {
      setError(err instanceof ApiError ? String(err.detail) : 'Unable to reset your password.');
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return <FormError message="Missing or invalid reset token. Please request a new reset link." />;
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Reset your password</h2>
      <FormError message={error} />
      <FormSuccess message={success} />

      <div>
        <FormField label="New password" htmlFor="password" />
        <FormInput
          id="password"
          type="password"
          required
          minLength={10}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="new-password"
        />
      </div>

      <FormButton type="submit" loading={loading}>
        Reset password
      </FormButton>

      <p className="text-center text-sm text-slate-500 dark:text-slate-400">
        <Link href="/login" className="font-medium text-cyan-600 hover:underline dark:text-cyan-300">
          Back to sign in
        </Link>
      </p>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordForm />
    </Suspense>
  );
}
