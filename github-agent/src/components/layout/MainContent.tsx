'use client'

import { useEffect } from 'react'
import { useAppViewStore } from '@/store/appViewStore'
import { useSettingsStore } from '@/store/settingsStore'
import { useChatStore } from '@/store/chatStore'
import { ChatsPanel } from '@/components/chats/ChatsPanel'
import { ChatInterface } from '@/components/chat/ChatInterface'

export function MainContent() {
  const mainView = useAppViewStore((s) => s.mainView)
  const chatsSubview = useAppViewStore((s) => s.chatsSubview)
  const openChat = useAppViewStore((s) => s.openChat)
  const loadSettings = useSettingsStore((s) => s.load)
  const pendingStarterPrompt = useChatStore((s) => s.pendingStarterPrompt)

  useEffect(() => {
    void loadSettings()
  }, [loadSettings])

  useEffect(() => {
    if (pendingStarterPrompt) {
      openChat()
    }
  }, [pendingStarterPrompt, openChat])

  const showChat = mainView === 'chats' && chatsSubview === 'chat'
  const showList = mainView === 'chats' && chatsSubview === 'list'

  return (
    <div className="flex flex-1 min-h-0 flex-col overflow-hidden">
      {/* Keep ChatInterface mounted so in-flight streams survive view switches */}
      <div className={showChat ? 'flex flex-1 min-h-0 flex-col' : 'hidden'}>
        <ChatInterface />
      </div>
      {showList ? <ChatsPanel /> : null}
    </div>
  )
}
