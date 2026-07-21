'use client';

import { useEffect } from 'react';

export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <p className="text-sm font-semibold uppercase tracking-[0.3em] text-red-500">500</p>
      <h1 className="mt-3 text-3xl font-semibold text-slate-900 dark:text-white">Something went wrong</h1>
      <p className="mt-2 max-w-sm text-sm text-slate-500 dark:text-slate-400">
        An unexpected error occurred. You can try again, or head back to the dashboard.
      </p>
      <div className="mt-6 flex gap-3">
        <button
          type="button"
          onClick={reset}
          className="rounded-xl bg-cyan-500 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400"
        >
          Try again
        </button>
        <a
          href="/dashboard"
          className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          Back to dashboard
        </a>
      </div>
    </div>
  );
}
