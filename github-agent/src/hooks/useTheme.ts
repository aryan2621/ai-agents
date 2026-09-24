'use client'

import { useEffect } from 'react'
import { useSettingsStore } from '@/store/settingsStore'
import { applyTheme, resolveTheme } from '@/lib/theme'
import type { ThemeMode } from '@/types'

export function useTheme() {
  const theme = useSettingsStore((s) => s.settings.theme)
  const update = useSettingsStore((s) => s.update)

  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  useEffect(() => {
    if (theme !== 'system') return

    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = () => applyTheme('system')
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [theme])

  const cycleTheme = () => {
    const order: ThemeMode[] = ['light', 'dark', 'system']
    const next = order[(order.indexOf(theme) + 1) % order.length]
    update({ theme: next })
  }

  const setTheme = (mode: ThemeMode) => {
    update({ theme: mode })
  }

  return {
    theme,
    resolved: resolveTheme(theme),
    cycleTheme,
    setTheme,
  }
}
