import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="min-h-screen bg-slate-50 p-10 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <nav className="mx-auto mb-8 flex max-w-6xl items-center justify-between text-sm text-slate-600 dark:text-slate-300">
        <span className="text-lg font-semibold text-slate-900 dark:text-white">CommerceOS</span>
        <div className="flex gap-4">
          <Link href="/dashboard" className="transition hover:text-slate-900 dark:hover:text-white">
            Dashboard
          </Link>
          <Link href="/login" className="transition hover:text-slate-900 dark:hover:text-white">
            Sign in
          </Link>
        </div>
      </nav>
      <div className="mx-auto max-w-6xl rounded-3xl border border-slate-200 bg-white p-10 shadow-2xl shadow-slate-200/50 dark:border-slate-800 dark:bg-slate-900/80 dark:shadow-black/20">
        <h1 className="text-4xl font-semibold tracking-tight text-slate-900 dark:text-white">CommerceOS</h1>
        <p className="mt-4 max-w-2xl text-lg text-slate-600 dark:text-slate-300">
          AI-first commerce operating system for modern teams. Explore your organization dashboard and manage billing, users, and operations from one central workspace.
        </p>
        <div className="mt-8 flex flex-col gap-4 sm:flex-row">
          <Link href="/dashboard" className="inline-flex items-center justify-center rounded-full bg-cyan-500 px-6 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-cyan-500/20 transition hover:bg-cyan-400">
            Open Dashboard
          </Link>
        </div>
      </div>
    </main>
  );
}
