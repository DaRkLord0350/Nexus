'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';
import { ApiError } from '@/lib/api-client';
import { verifyEmail } from '@/lib/auth';
import { FormError, FormSuccess } from '@/components/ui/form';

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token') ?? '';
  const [status, setStatus] = useState<'pending' | 'success' | 'error'>('pending');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setError('Missing verification token.');
      return;
    }
    verifyEmail(token)
      .then(() => setStatus('success'))
      .catch((err) => {
        setStatus('error');
        setError(err instanceof ApiError ? String(err.detail) : 'Unable to verify your email.');
      });
  }, [token]);

  return (
    <div className="space-y-4 text-center">
      <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Email verification</h2>
      {status === 'pending' ? <p className="text-sm text-slate-500 dark:text-slate-400">Verifying your email…</p> : null}
      {status === 'success' ? <FormSuccess message="Your email has been verified successfully." /> : null}
      {status === 'error' ? <FormError message={error} /> : null}
      <p className="text-sm text-slate-500 dark:text-slate-400">
        <Link href="/login" className="font-medium text-cyan-600 hover:underline dark:text-cyan-300">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={null}>
      <VerifyEmailContent />
    </Suspense>
  );
}
