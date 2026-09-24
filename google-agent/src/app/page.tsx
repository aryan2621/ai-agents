'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { isOnboardingComplete } from '@/lib/onboarding'

export default function HomePage() {
  const router = useRouter()
  const { isAuthenticated, isLoading } = useAuthStore()
  const [checkingOnboarding, setCheckingOnboarding] = useState(true)

  useEffect(() => {
    let cancelled = false
    void isOnboardingComplete().then((complete) => {
      if (cancelled) return
      setCheckingOnboarding(false)
      if (!complete) {
        router.replace('/onboarding')
        return
      }
      if (!isLoading) {
        router.replace(isAuthenticated ? '/chat' : '/auth')
      }
    })
    return () => {
      cancelled = true
    }
  }, [isAuthenticated, isLoading, router])

  useEffect(() => {
    if (checkingOnboarding || isLoading) return
    void isOnboardingComplete().then((complete) => {
      if (complete) {
        router.replace(isAuthenticated ? '/chat' : '/auth')
      }
    })
  }, [checkingOnboarding, isAuthenticated, isLoading, router])

  return (
    <div className="flex-1 min-h-0 flex items-center justify-center bg-background">
      <div className="w-5 h-5 border-2 border-muted border-t-muted-foreground rounded-full animate-spin" />
    </div>
  )
}
