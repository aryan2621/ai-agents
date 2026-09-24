'use client'

import { useEffect } from 'react'

export function isMacOS() {
  return typeof navigator !== 'undefined' && /Mac|iPhone|iPad|iPod/.test(navigator.platform)
}

export function usePlatform() {
  useEffect(() => {
    if (isMacOS()) {
      document.documentElement.classList.add('platform-macos')
    }
    return () => {
      document.documentElement.classList.remove('platform-macos')
    }
  }, [])
}
