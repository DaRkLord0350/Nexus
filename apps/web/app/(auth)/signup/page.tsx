'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState, type FormEvent } from 'react';
import { ApiError } from '@/lib/api-client';
import { login, signup } from '@/lib/auth';
import { FormButton, FormError, FormField, FormInput } from '@/components/ui/form';

export default function SignupPage() {
  const router = useRouter();
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [organizationName, setOrganizationName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await signup({ email, first_name: firstName, last_name: lastName, password, organization_name: organizationName });
      await login(email, password);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof ApiError ? String(err.detail) : 'Unable to create your account.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Create your organization</h2>
      <FormError message={error} />

      <div className="grid grid-cols-2 gap-3">
        <div>
          <FormField label="First name" htmlFor="firstName" />
          <FormInput id="firstName" required value={firstName} onChange={(e) => setFirstName(e.target.value)} autoComplete="given-name" />
        </div>
        <div>
          <FormField label="Last name" htmlFor="lastName" />
          <FormInput id="lastName" required value={lastName} onChange={(e) => setLastName(e.target.value)} autoComplete="family-name" />
        </div>
      </div>

      <div>
        <FormField label="Organization name" htmlFor="organizationName" />
        <FormInput id="organizationName" required value={organizationName} onChange={(e) => setOrganizationName(e.target.value)} />
      </div>

      <div>
        <FormField label="Email" htmlFor="email" />
        <FormInput id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
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
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">At least 10 characters.</p>
      </div>

      <FormButton type="submit" loading={loading}>
        Create account
      </FormButton>

      <p className="text-center text-sm text-slate-500 dark:text-slate-400">
        Already have an account?{' '}
        <Link href="/login" className="font-medium text-cyan-600 hover:underline dark:text-cyan-300">
          Sign in
        </Link>
      </p>
    </form>
  );
}
