'use client'

import { useEffect } from 'react'
import { useSettingsStore } from '@/store/settingsStore'
import { applyFontSize } from '@/lib/fontSize'

export function useFontSize() {
  const fontSize = useSettingsStore((s) => s.settings.fontSize)

  useEffect(() => {
    applyFontSize(fontSize)
  }, [fontSize])
}
