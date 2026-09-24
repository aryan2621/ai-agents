'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { Sidebar } from '@/components/sidebar/Sidebar'
import { MainContent } from '@/components/layout/MainContent'

export default function ChatPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading } = useAuthStore()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace('/auth')
  }, [isAuthenticated, isLoading, router])

  if (isLoading) {
    return (
      <div className="flex-1 min-h-0 flex items-center justify-center bg-background">
        <div className="w-5 h-5 border-2 border-muted border-t-muted-foreground rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="flex-1 min-h-0 flex overflow-hidden bg-background">
      <Sidebar />
      <MainContent />
    </div>
  )
}
