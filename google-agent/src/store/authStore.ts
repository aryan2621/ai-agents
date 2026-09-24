import { create } from 'zustand'
import { HTTPError } from 'ky'
import { sessionStore } from '@/lib/session-store'
import { fetchMe, logout, waitForBackend } from '@/lib/api'
import { cancelActiveStream } from '@/lib/streaming'
import type { GoogleUser } from '@/types'

interface AuthState {
  user: GoogleUser | null
  isAuthenticated: boolean
  isLoading: boolean
  setUser: (user: GoogleUser) => Promise<void>
  clearUser: () => Promise<void>
  loadFromStore: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  setUser: async (user) => {
    await sessionStore.setAccessToken(user.accessToken)
    set({ user, isAuthenticated: true, isLoading: false })
  },

  clearUser: async () => {
    cancelActiveStream()
    try {
      await logout()
    } catch {
      // session may already be invalid
    }
    await sessionStore.clearAccessToken()
    const { useChatStore } = await import('@/store/chatStore')
    const { useSettingsStore } = await import('@/store/settingsStore')
    useChatStore.setState({ conversations: [], activeId: null, isGenerating: false })
    useSettingsStore.getState().load().catch(() => {})
    set({ user: null, isAuthenticated: false, isLoading: false })
  },

  loadFromStore: async () => {
    const token = await sessionStore.getAccessToken()
    if (!token) {
      set({ user: null, isAuthenticated: false, isLoading: false })
      return
    }

    const backendUp = await waitForBackend()
    if (!backendUp) {
      // Keep token on disk — backend may still be starting after dev restart
      set({ user: null, isAuthenticated: false, isLoading: false })
      return
    }

    try {
      const user = await fetchMe(token)
      await sessionStore.setAccessToken(user.accessToken)
      set({ user, isAuthenticated: true, isLoading: false })
    } catch (err) {
      if (err instanceof HTTPError && err.response.status === 401) {
        await sessionStore.clearAccessToken()
      }
      set({ user: null, isAuthenticated: false, isLoading: false })
    }
  },
}))
