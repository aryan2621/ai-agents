'use client'

import { useCallback } from 'react'
import { invoke } from '@tauri-apps/api/core'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { useAuthStore } from '@/store/authStore'
import { focusAppWindow } from '@/lib/focusApp'
import { API_BASE_URL } from '@/lib/config'
import {
  markOAuthStateComplete,
  setOAuthNavigate,
  shouldNavigateAfterOAuth,
} from '@/lib/oauth-flow'
import type { GoogleUser } from '@/types'

const POLL_INTERVAL_MS = 1000
const POLL_TIMEOUT_MS = 120_000

async function pollAuthStatus(state: string): Promise<GoogleUser | null> {
  const deadline = Date.now() + POLL_TIMEOUT_MS

  while (Date.now() < deadline) {
    const response = await fetch(`${API_BASE_URL}/auth/google/status/${state}`)
    if (response.ok) {
      return response.json() as Promise<GoogleUser>
    }
    if (response.status !== 404) {
      const body = await response.json().catch(() => ({}))
      const detail = typeof body.detail === 'string' ? body.detail : 'Authentication failed'
      throw new Error(detail)
    }
    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS))
  }

  return null
}

interface SignInOptions {
  navigate?: boolean
  successMessage?: string
}

export function useGoogleAuth() {
  const router = useRouter()
  const setUser = useAuthStore((s) => s.setUser)

  const signInWithGoogle = useCallback(
    async (options?: SignInOptions) => {
      setOAuthNavigate(options?.navigate !== false)
      const state = await invoke<string>('start_google_auth')
      toast.message('Click “Continue with Google” in the browser tab to sign in.')

      const user = await pollAuthStatus(state)
      if (!user) {
        throw new Error('Timed out waiting for Google sign-in. Close the browser tab and try again.')
      }

      if (!markOAuthStateComplete(state)) {
        return user
      }

      await setUser(user)
      await focusAppWindow()
      toast.success(options?.successMessage ?? 'Signed in successfully')

      if (shouldNavigateAfterOAuth()) {
        router.push('/chat')
      }

      return user
    },
    [router, setUser]
  )

  return { signInWithGoogle }
}
