import { NotificationCenter } from '@/components/notification-center';

export default function DashboardNotificationsPage() {
  return (
    <main className="space-y-8">
      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-lg shadow-slate-200/50 dark:border-slate-800 dark:bg-slate-900/90 dark:shadow-black/10">
        <div className="space-y-2">
          <p className="text-sm text-slate-500 dark:text-slate-400">Updates</p>
          <h1 className="text-3xl font-semibold text-slate-900 dark:text-white">Notifications</h1>
          <p className="text-sm text-slate-600 dark:text-slate-300">Stay on top of important system events, messages, and alerts.</p>
        </div>
      </div>
      <NotificationCenter />
    </main>
  );
}
