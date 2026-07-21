import type { Metadata } from 'next';
import './globals.css';
import { GlobalThemeToggle } from '@/components/global-theme-toggle';
import { THEME_INIT_SCRIPT } from '@/lib/theme';

export const metadata: Metadata = {
  title: 'CommerceOS',
  description: 'AI-first Commerce Operating System dashboard',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
        <GlobalThemeToggle />
        {children}
      </body>
    </html>
  );
}
