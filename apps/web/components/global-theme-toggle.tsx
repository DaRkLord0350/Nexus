'use client';

import { usePathname } from 'next/navigation';
import { ThemeToggle } from '@/components/theme-toggle';

export function GlobalThemeToggle() {
  const pathname = usePathname();
  if (pathname?.startsWith('/dashboard')) {
    return null;
  }
  return (
    <div className="fixed right-4 top-4 z-40">
      <ThemeToggle />
    </div>
  );
}
