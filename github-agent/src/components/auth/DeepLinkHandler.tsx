'use client'

import { onOpenUrl } from '@tauri-apps/plugin-deep-link'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { toast } from 'sonner'
import { focusAppWindow } from '@/lib/focusApp'
import { API_BASE_URL } from '@/lib/config'
import {
  markOAuthStateComplete,
  shouldNavigateAfterOAuth,
} from '@/lib/oauth-flow'
import type { GitHubUser } from '@/types'

async function fetchAuthResult(state: string): Promise<GitHubUser> {
  const response = await fetch(`${API_BASE_URL}/auth/github/status/${state}`)
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const detail = typeof body.detail === 'string' ? body.detail : 'Authentication failed'
    throw new Error(detail)
  }
  return response.json() as Promise<GitHubUser>
}

export function DeepLinkHandler() {
  const router = useRouter()
  const setUser = useAuthStore((s) => s.setUser)

  useEffect(() => {
    const setup = async () => {
      const unlisten = await onOpenUrl(async (urls) => {
        for (const url of urls) {
          if (!url.startsWith('github-agent://oauth/callback')) continue

          const urlObj = new URL(url)
          const error = urlObj.searchParams.get('error')
          if (error) {
            toast.error(`GitHub sign-in failed: ${error}`)
            return
          }

          const state = urlObj.searchParams.get('state')
          if (!state) {
            toast.error('Missing OAuth state in callback')
            return
          }

          if (!markOAuthStateComplete(state)) return

          try {
            const userData = await fetchAuthResult(state)
            await setUser(userData)
            await focusAppWindow()
            toast.success('Signed in successfully')
            if (shouldNavigateAfterOAuth()) {
              router.push('/chat')
            }
          } catch (err) {
            toast.error(err instanceof Error ? err.message : 'Authentication failed')
          }
        }
      })
      return unlisten
    }

    let cleanup: (() => void) | undefined
    setup().then((fn) => {
      cleanup = fn
    })
    return () => {
      cleanup?.()
    }
  }, [router, setUser])

  return null
}
