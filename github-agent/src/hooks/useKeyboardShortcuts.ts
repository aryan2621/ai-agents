'use client'

import { useEffect } from 'react'
import { useChatStore } from '@/store/chatStore'
import { useAppViewStore } from '@/store/appViewStore'

let settingsOpenHandler: (() => void) | null = null

export function registerSettingsOpenHandler(handler: () => void) {
  settingsOpenHandler = handler
}

export function openSettingsModal() {
  settingsOpenHandler?.()
}

export function useKeyboardShortcuts() {
  const startNewChat = useChatStore((s) => s.startNewChat)
  const openChat = useAppViewStore((s) => s.openChat)
  const toggleSidebar = useAppViewStore((s) => s.toggleSidebar)

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const mod = e.metaKey || e.ctrlKey

      if (mod && e.key === 'n') {
        e.preventDefault()
        startNewChat()
        openChat()
        return
      }

      if (mod && e.key === 'b') {
        e.preventDefault()
        toggleSidebar()
        return
      }

      if (mod && e.key === ',') {
        e.preventDefault()
        settingsOpenHandler?.()
      }
    }

    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [startNewChat, openChat, toggleSidebar])
}
