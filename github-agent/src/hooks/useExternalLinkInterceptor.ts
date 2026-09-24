'use client'

import { useEffect } from 'react'
import { interceptExternalLinkClick, isTauriRuntime } from '@/lib/open-external'

export function useExternalLinkInterceptor() {
  useEffect(() => {
    if (!isTauriRuntime()) return

    const onClickCapture = (event: MouseEvent) => {
      interceptExternalLinkClick(event)
    }

    document.addEventListener('click', onClickCapture, true)
    return () => document.removeEventListener('click', onClickCapture, true)
  }, [])
}
