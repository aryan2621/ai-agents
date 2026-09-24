import type { ThemeMode } from '@/types'

const THEME_STORAGE_KEY = 'google-agent-theme'

export function resolveTheme(mode: ThemeMode): 'light' | 'dark' {
  if (mode === 'system') {
    if (typeof window === 'undefined') return 'dark'
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return mode
}

export function applyTheme(mode: ThemeMode) {
  const resolved = resolveTheme(mode)
  const root = document.documentElement
  root.classList.remove('light', 'dark')
  root.classList.add(resolved)
  try {
    localStorage.setItem(THEME_STORAGE_KEY, mode)
  } catch {
    // ignore storage errors
  }
}

export function getStoredTheme(): ThemeMode | null {
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY)
    if (stored === 'light' || stored === 'dark' || stored === 'system') {
      return stored
    }
  } catch {
    // ignore storage errors
  }
  return null
}

export const themeInitScript = `
(function() {
  try {
    var stored = localStorage.getItem('${THEME_STORAGE_KEY}');
    var mode = stored === 'light' || stored === 'dark' || stored === 'system' ? stored : 'system';
    var resolved = mode === 'system'
      ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
      : mode;
    document.documentElement.classList.add(resolved);
    document.documentElement.style.setProperty('--app-height', window.innerHeight + 'px');
  } catch (e) {
    document.documentElement.classList.add('dark');
  }
})();
`
