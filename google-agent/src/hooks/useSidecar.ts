'use client'

import { useEffect, useState } from 'react'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { API_BASE_URL } from '@/lib/config'

export function useSidecar() {
  const [isHealthy, setIsHealthy] = useState(false)
  const [isChecking, setIsChecking] = useState(true)
  const [lastError, setLastError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/health`, {
          signal: AbortSignal.timeout(3000),
        })
        if (!cancelled) {
          setIsHealthy(response.ok)
        }
      } catch {
        try {
          const healthy = await invoke<boolean>('check_backend_health')
          if (!cancelled) setIsHealthy(healthy)
        } catch {
          if (!cancelled) setIsHealthy(false)
        }
      } finally {
        if (!cancelled) setIsChecking(false)
      }
    }

    checkHealth()
    const interval = setInterval(checkHealth, 1000)

    const unlistenReady = listen('backend-ready', () => {
      setIsHealthy(true)
      setIsChecking(false)
    })
    const unlistenErr = listen<string>('backend-error', (e) => {
      setLastError(e.payload)
      setIsHealthy(false)
    })

    return () => {
      cancelled = true
      clearInterval(interval)
      unlistenReady.then((fn) => fn())
      unlistenErr.then((fn) => fn())
    }
  }, [])

  return { isHealthy, isChecking, lastError }
}
