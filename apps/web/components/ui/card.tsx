interface DashboardCardProps {
  title: string;
  value: number;
  subtitle?: string;
}

export function DashboardCard({ title, value, subtitle }: DashboardCardProps) {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-lg shadow-slate-200/50 dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-black/10">
      <p className="text-sm font-medium uppercase tracking-[0.24em] text-cyan-600 dark:text-cyan-300">{title}</p>
      <p className="mt-4 text-4xl font-semibold text-slate-900 dark:text-white">{value}</p>
      {subtitle ? <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">{subtitle}</p> : null}
    </article>
  );
}
