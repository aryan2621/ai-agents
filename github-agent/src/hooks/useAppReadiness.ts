'use client'

import { useReadinessStore } from '@/store/readinessStore'

export function useAppReadiness() {
  const loading = useReadinessStore((s) => s.loading)
  const ready = useReadinessStore((s) => s.ready)
  const issues = useReadinessStore((s) => s.issues)
  const check = useReadinessStore((s) => s.check)

  return {
    loading,
    ready,
    issues,
    retry: () => check({ forceLoading: true }),
  }
}
