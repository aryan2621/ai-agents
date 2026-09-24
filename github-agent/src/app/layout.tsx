'use client'

import dynamic from 'next/dynamic'
import { useEffect } from 'react'
import { listen } from '@tauri-apps/api/event'
import { useAuthStore } from '@/store/authStore'
import { sessionStore } from '@/lib/session-store'
import { useChatStore } from '@/store/chatStore'
import { useSettingsStore } from '@/store/settingsStore'
import { useReadinessStore } from '@/store/readinessStore'
import { Toaster } from '@/components/ui/sonner'
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts'
import { useReadinessPoll } from '@/hooks/useReadinessPoll'
import { useExternalLinkInterceptor } from '@/hooks/useExternalLinkInterceptor'
import { useTheme } from '@/hooks/useTheme'
import { useFontSize } from '@/hooks/useFontSize'
import { useWindowHeight } from '@/hooks/useWindowHeight'
import { usePlatform } from '@/hooks/usePlatform'
import { themeInitScript } from '@/lib/theme'
import { fontSizeInitScript } from '@/lib/fontSize'
import './globals.css'

const TitleBar = dynamic(
  () => import('@/components/layout/TitleBar').then((m) => m.TitleBar),
  { ssr: false }
)

const DeepLinkHandler = dynamic(
  () => import('@/components/auth/DeepLinkHandler').then((m) => m.DeepLinkHandler),
  { ssr: false }
)

function MacDragRegion() {
  return (
    <div
      data-tauri-drag-region
      className="mac-drag-region shrink-0 w-full"
    />
  )
}

function AppShell({ children }: { children: React.ReactNode }) {
  const loadAuth = useAuthStore((s) => s.loadFromStore)
  const loadChats = useChatStore((s) => s.loadConversations)
  const loadSettings = useSettingsStore((s) => s.load)

  useTheme()
  useFontSize()
  useWindowHeight()
  usePlatform()

  useEffect(() => {
    loadAuth()

    let unlisten: (() => void) | undefined
    listen('backend-ready', () => {
      void useReadinessStore.getState().check({ silent: true })
      const { isAuthenticated, isLoading } = useAuthStore.getState()
      if (!isAuthenticated && !isLoading) {
        void sessionStore.getAccessToken().then((token) => {
          if (token) loadAuth()
        })
      }
    }).then((fn) => {
      unlisten = fn
    })

    return () => {
      unlisten?.()
    }
  }, [loadAuth])

  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const isLoading = useAuthStore((s) => s.isLoading)

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      loadChats()
      loadSettings()
    }
  }, [isLoading, isAuthenticated, loadChats, loadSettings])

  useKeyboardShortcuts()
  useReadinessPoll()
  useExternalLinkInterceptor()

  return (
    <div className="flex flex-col h-full min-h-0 w-full overflow-hidden">
      <MacDragRegion />
      <TitleBar />
      <DeepLinkHandler />
      <main className="flex flex-col flex-1 min-h-0 overflow-hidden">{children}</main>
      <Toaster theme="system" position="bottom-right" />
    </div>
  )
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/app-icon.png" />
        <script dangerouslySetInnerHTML={{ __html: themeInitScript + fontSizeInitScript }} />
      </head>
      <body className="bg-background text-foreground flex flex-col font-sans">
        <div className="flex flex-col h-full min-h-0 w-full">
          <AppShell>{children}</AppShell>
        </div>
      </body>
    </html>
  )
}
