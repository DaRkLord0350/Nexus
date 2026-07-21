'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useState, type FormEvent } from 'react';
import { ApiError } from '@/lib/api-client';
import { acceptInvitation, login } from '@/lib/auth';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';

function AcceptInviteForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token') ?? '';
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user = await acceptInvitation({ token, first_name: firstName, last_name: lastName, password });
      await login(user.email, password);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof ApiError ? String(err.detail) : 'Unable to accept this invitation.');
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return <FormError message="Missing or invalid invitation token." />;
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Join your team</h2>
      <FormError message={error} />

      <div className="grid grid-cols-2 gap-3">
        <div>
          <FormField label="First name" htmlFor="firstName" />
          <FormInput id="firstName" required value={firstName} onChange={(e) => setFirstName(e.target.value)} />
        </div>
        <div>
          <FormField label="Last name" htmlFor="lastName" />
          <FormInput id="lastName" required value={lastName} onChange={(e) => setLastName(e.target.value)} />
        </div>
      </div>

      <div>
        <FormField label="Password" htmlFor="password" />
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
        Accept invitation
      </FormButton>

      <p className="text-center text-sm text-slate-500 dark:text-slate-400">
        <Link href="/login" className="font-medium text-cyan-600 hover:underline dark:text-cyan-300">
          Back to sign in
        </Link>
      </p>
    </form>
  );
}

export default function AcceptInvitePage() {
  return (
    <Suspense fallback={null}>
      <AcceptInviteForm />
    </Suspense>
  );
}
