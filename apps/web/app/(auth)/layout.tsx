import type { ReactNode } from 'react';

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-[80vh] items-center justify-center">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <p className="text-xs uppercase tracking-[0.3em] text-cyan-600 dark:text-cyan-300">CommerceOS</p>
          <h1 className="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">Commerce Operating System</h1>
        </div>
        <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-xl shadow-slate-200/50 dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-black/20">
          {children}
        </div>
      </div>
    </div>
  );
}
