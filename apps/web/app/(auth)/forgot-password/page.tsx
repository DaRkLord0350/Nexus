'use client';

import Link from 'next/link';
import { useState, type FormEvent } from 'react';
import { forgotPassword } from '@/lib/auth';
import { FormButton, FormError, FormField, FormInput, FormSuccess } from '@/components/ui/form';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);
    try {
      await forgotPassword(email);
      setSuccess('If an account exists for that email, reset instructions have been sent.');
    } catch {
      setError('Unable to process your request.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Forgot your password?</h2>
      <p className="text-sm text-slate-500 dark:text-slate-400">Enter your email and we&apos;ll send you a reset link.</p>
      <FormError message={error} />
      <FormSuccess message={success} />

      <div>
        <FormField label="Email" htmlFor="email" />
        <FormInput id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
      </div>

      <FormButton type="submit" loading={loading}>
        Send reset link
      </FormButton>

      <p className="text-center text-sm text-slate-500 dark:text-slate-400">
        <Link href="/login" className="font-medium text-cyan-600 hover:underline dark:text-cyan-300">
          Back to sign in
        </Link>
      </p>
    </form>
  );
}
