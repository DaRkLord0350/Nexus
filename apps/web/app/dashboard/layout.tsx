import type { ReactNode } from 'react';
import { AuthProvider } from '@/components/auth-provider';
import { Header } from '@/components/header';
import { Sidebar } from '@/components/sidebar';

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
        <div className="flex min-h-screen">
          <Sidebar />
          <div className="flex min-h-screen flex-1 flex-col">
            <Header />
            <section className="flex-1 px-6 py-8 lg:px-10">{children}</section>
          </div>
        </div>
      </div>
    </AuthProvider>
  );
}
