'use client'

import { useSidecar } from '@/hooks/useSidecar'

export function BackendStatusBanner() {
  const { isHealthy, isChecking, lastError } = useSidecar()

  if (isChecking || isHealthy) return null

  return (
    <div className="shrink-0 bg-destructive/10 border-b border-destructive/30 px-4 py-2 text-app-caption text-destructive">
      Backend unavailable. Restart the app or run{' '}
      <code className="font-mono">npm run build:sidecar</code> if the backend failed to start.
      {lastError ? (
        <span className="block mt-1 text-muted-foreground truncate">{lastError}</span>
      ) : null}
    </div>
  )
}
