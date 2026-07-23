'use client';

import { useRouter } from 'next/navigation';
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { clearCustomerOrgId, clearCustomerToken, getCustomerToken } from '@/lib/customer-portal/api-client';
import { fetchMyProfile } from '@/lib/customer-portal/auth';
import type { CustomerItem } from '@/lib/types';

interface CustomerAuthContextValue {
  customer: CustomerItem | null;
  isLoading: boolean;
  logout: () => void;
  refresh: () => Promise<void>;
}

const CustomerAuthContext = createContext<CustomerAuthContextValue | null>(null);

export function CustomerAuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [customer, setCustomer] = useState<CustomerItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    const token = getCustomerToken();
    if (!token) {
      setCustomer(null);
      setIsLoading(false);
      router.replace('/portal/login');
      return;
    }

    try {
      const profile = await fetchMyProfile();
      setCustomer(profile);
    } catch {
      setCustomer(null);
      router.replace('/portal/login');
    } finally {
      setIsLoading(false);
    }
  }, [router]);

  useEffect(() => {
    load();
  }, [load]);

  const handleLogout = useCallback(() => {
    clearCustomerToken();
    clearCustomerOrgId();
    setCustomer(null);
    router.replace('/portal/login');
  }, [router]);

  const value = useMemo<CustomerAuthContextValue>(
    () => ({ customer, isLoading, logout: handleLogout, refresh: load }),
    [customer, isLoading, handleLogout, load],
  );

  return <CustomerAuthContext.Provider value={value}>{children}</CustomerAuthContext.Provider>;
}

export function useCustomerAuth(): CustomerAuthContextValue {
  const context = useContext(CustomerAuthContext);
  if (!context) {
    throw new Error('useCustomerAuth must be used within a CustomerAuthProvider');
  }
  return context;
}
