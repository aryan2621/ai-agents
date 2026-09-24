'use client'

import { useEffect } from 'react'
import { useReadinessStore } from '@/store/readinessStore'

export function useReadinessPoll() {
  const check = useReadinessStore((s) => s.check)

  useEffect(() => {
    void check()

    const interval = setInterval(() => void check({ silent: true }), 5000)
    const onConnectivityChange = () => void check({ silent: true })
    window.addEventListener('online', onConnectivityChange)
    window.addEventListener('offline', onConnectivityChange)

    return () => {
      clearInterval(interval)
      window.removeEventListener('online', onConnectivityChange)
      window.removeEventListener('offline', onConnectivityChange)
    }
  }, [check])
}
