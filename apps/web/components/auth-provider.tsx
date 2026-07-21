'use client';

import { useRouter } from 'next/navigation';
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { getAccessToken } from '@/lib/api-client';
import { getCurrentUser, getMyPermissions, logout as logoutRequest } from '@/lib/auth';
import type { Permission, User } from '@/lib/types';

interface AuthContextValue {
  user: User | null;
  permissions: string[];
  isLoading: boolean;
  hasPermission: (code: string) => boolean;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setUser(null);
      setPermissions([]);
      setIsLoading(false);
      router.replace('/login');
      return;
    }

    try {
      const [currentUser, myPermissions] = await Promise.all([getCurrentUser(), getMyPermissions()]);
      setUser(currentUser);
      setPermissions(myPermissions.map((permission: Permission) => permission.code));
    } catch {
      setUser(null);
      setPermissions([]);
      router.replace('/login');
    } finally {
      setIsLoading(false);
    }
  }, [router]);

  useEffect(() => {
    load();
  }, [load]);

  const handleLogout = useCallback(async () => {
    await logoutRequest();
    setUser(null);
    setPermissions([]);
    router.replace('/login');
  }, [router]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      permissions,
      isLoading,
      hasPermission: (code: string) => permissions.includes(code),
      logout: handleLogout,
      refresh: load,
    }),
    [user, permissions, isLoading, handleLogout, load],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
