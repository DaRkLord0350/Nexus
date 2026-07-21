export const THEME_STORAGE_KEY = 'commerceos-theme';

export type Theme = 'dark' | 'light';

export function getStoredTheme(): Theme {
  if (typeof window === 'undefined') {
    return 'dark';
  }
  const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
  return stored === 'light' ? 'light' : 'dark';
}

export function applyTheme(theme: Theme): void {
  if (typeof document === 'undefined') {
    return;
  }
  document.documentElement.classList.toggle('dark', theme === 'dark');
  document.documentElement.classList.toggle('light', theme === 'light');
  window.localStorage.setItem(THEME_STORAGE_KEY, theme);
}

export const THEME_INIT_SCRIPT = `
(function () {
  try {
    var stored = window.localStorage.getItem('${THEME_STORAGE_KEY}');
    var theme = stored === 'light' ? 'light' : 'dark';
    document.documentElement.classList.add(theme);
  } catch (e) {
    document.documentElement.classList.add('dark');
  }
})();
`;
