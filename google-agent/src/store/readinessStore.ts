import { create } from 'zustand'
import { fetchHealth } from '@/lib/api'
import type { ReadinessIssue } from '@/types'

interface ReadinessState {
  loading: boolean
  ready: boolean
  issues: ReadinessIssue[]
  initialized: boolean
  check: (options?: { silent?: boolean; forceLoading?: boolean }) => Promise<void>
}

export const useReadinessStore = create<ReadinessState>((set, get) => ({
  loading: true,
  ready: false,
  issues: [],
  initialized: false,

  check: async (options) => {
    const silent = options?.silent ?? false
    const forceLoading = options?.forceLoading ?? false
    const { initialized } = get()

    if (forceLoading || (!silent && !initialized)) {
      set({ loading: true })
    }

    if (typeof navigator !== 'undefined' && !navigator.onLine) {
      set({
        loading: false,
        ready: false,
        initialized: true,
        issues: [
          {
            code: 'network',
            message: 'No internet connection.',
            remediation: 'Connect to the internet — Google Workspace requires network access.',
          },
        ],
      })
      return
    }

    try {
      const health = await fetchHealth()
      set({
        loading: false,
        ready: health.ready,
        initialized: true,
        issues: health.issues,
      })
    } catch {
      set({
        loading: false,
        ready: false,
        initialized: true,
        issues: [
          {
            code: 'backend',
            message: 'Backend is not running.',
            remediation: 'Restart the app or run npm run build:sidecar if the backend failed to start.',
          },
        ],
      })
    }
  },
}))
