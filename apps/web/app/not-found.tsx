import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <p className="text-sm font-semibold uppercase tracking-[0.3em] text-cyan-600 dark:text-cyan-300">404</p>
      <h1 className="mt-3 text-3xl font-semibold text-slate-900 dark:text-white">Page not found</h1>
      <p className="mt-2 max-w-sm text-sm text-slate-500 dark:text-slate-400">
        The page you&apos;re looking for doesn&apos;t exist or may have been moved.
      </p>
      <Link
        href="/dashboard"
        className="mt-6 rounded-xl bg-cyan-500 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400"
      >
        Back to dashboard
      </Link>
    </div>
  );
}
