import { create } from 'zustand'
import {
  clearAllConversationsApi,
  createConversationApi,
  createMessageApi,
  deleteConversationApi,
  deleteConversationsApi,
  editMessageAndTruncateApi,
  fetchConversationApi,
  fetchConversations,
  generateConversationTitleApi,
  renameConversationApi,
  updateMessageApi,
} from '@/lib/api'
import type { Conversation, Message, PendingStarter, Settings } from '@/types'
import type { RoomAgentName } from '@/lib/agents'
import { nanoid } from 'nanoid'

interface ChatState {
  conversations: Conversation[]
  activeId: string | null
  isGenerating: boolean
  isLoadingChats: boolean
  isSwitchingChat: boolean
  pendingAutoSend: { convId: string; text: string } | null
  pendingStarterPrompt: PendingStarter | null

  loadConversations: () => Promise<void>
  setActiveId: (id: string | null) => void
  startNewChat: () => void
  selectConversation: (id: string) => Promise<void>
  createConversation: (agentFilter: RoomAgentName) => Promise<string>
  saveDraft: (id: string) => Promise<void>
  deleteConversation: (id: string) => Promise<void>
  deleteConversations: (ids: string[]) => Promise<void>
  renameConversation: (id: string, title: string) => Promise<void>
  generateConversationTitle: (id: string, message: string, settings?: Settings) => Promise<void>
  addMessage: (convId: string, msg: Message) => void
  appendChunk: (convId: string, msgId: string, chunk: string) => void
  replaceContent: (convId: string, msgId: string, content: string) => void
  finalizeMessage: (convId: string, msgId: string, agentName?: Message['agentName'], error?: string) => Promise<void>
  editMessageAndTruncate: (convId: string, msgId: string, content: string) => Promise<void>
  setGenerating: (val: boolean) => void
  clearAllConversations: () => Promise<void>
  queueAutoSend: (convId: string, text: string) => void
  consumePendingAutoSend: () => { convId: string; text: string } | null
  setPendingStarterPrompt: (starter: PendingStarter | null) => void
  consumePendingStarterPrompt: () => PendingStarter | null
}

function truncateMessagesAfter(
  conversations: Conversation[],
  convId: string,
  msgId: string,
  content: string
): Conversation[] {
  return conversations.map((c) => {
    if (c.id !== convId) return c
    const idx = c.messages.findIndex((m) => m.id === msgId)
    if (idx === -1) return c
    return {
      ...c,
      updatedAt: new Date(),
      messages: c.messages.slice(0, idx + 1).map((m, i) =>
        i === idx ? { ...m, content } : m
      ),
    }
  })
}

/** Unsent drafts other than `keep`: leaving a draft discards it, so it never lingers. */
function withoutDrafts(conversations: Conversation[], keep?: string | null): Conversation[] {
  return conversations.filter((c) => !c.draft || c.id === keep)
}

function emptyConversation(id: string, agentFilter: RoomAgentName): Conversation {
  const now = new Date()
  return {
    id,
    title: 'New Chat',
    messages: [],
    createdAt: now,
    updatedAt: now,
    agentFilter,
  }
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  activeId: null,
  isGenerating: false,
  isLoadingChats: false,
  isSwitchingChat: false,
  pendingAutoSend: null,
  pendingStarterPrompt: null,

  loadConversations: async () => {
    set({ isLoadingChats: true })
    try {
      const convs = await fetchConversations()
      set((s) => ({ conversations: [...s.conversations.filter((c) => c.draft), ...convs] }))
    } catch {
      // ignore load failures; UI stays empty until retry
    } finally {
      set({ isLoadingChats: false })
    }
  },

  setActiveId: (id) =>
    set((s) => ({ activeId: id, conversations: withoutDrafts(s.conversations, id) })),

  startNewChat: () => set((s) => ({ activeId: null, conversations: withoutDrafts(s.conversations) })),

  selectConversation: async (id) => {
    set((s) => ({
      activeId: id,
      isSwitchingChat: true,
      conversations: withoutDrafts(s.conversations, id),
    }))
    const existing = get().conversations.find((c) => c.id === id)
    if (existing) {
      await new Promise((resolve) => requestAnimationFrame(() => resolve(undefined)))
      set({ isSwitchingChat: false })
      return
    }
    try {
      const conv = await fetchConversationApi(id)
      set((s) => ({
        conversations: s.conversations.some((c) => c.id === id)
          ? s.conversations.map((c) => (c.id === id ? conv : c))
          : [conv, ...s.conversations],
      }))
    } catch {
      await get().loadConversations()
    } finally {
      set({ isSwitchingChat: false })
    }
  },

  // Picking an agent only opens a draft; nothing is saved until the first message (saveDraft).
  createConversation: async (agentFilter) => {
    const id = nanoid()
    set((s) => ({
      conversations: [{ ...emptyConversation(id, agentFilter), draft: true }, ...withoutDrafts(s.conversations)],
      activeId: id,
    }))
    return id
  },

  saveDraft: async (id) => {
    const conv = get().conversations.find((c) => c.id === id)
    if (!conv?.draft) return
    const saved = await createConversationApi(id, conv.agentFilter as RoomAgentName)
    set((s) => ({
      conversations: s.conversations.map((c) =>
        c.id === id ? { ...saved, messages: c.messages, draft: false } : c
      ),
    }))
  },

  deleteConversation: async (id) => {
    await deleteConversationApi(id)
    set((s) => ({
      conversations: s.conversations.filter((c) => c.id !== id),
      activeId: s.activeId === id ? null : s.activeId,
    }))
  },

  deleteConversations: async (ids) => {
    if (ids.length === 0) return
    const idSet = new Set(ids)
    await deleteConversationsApi(ids)
    set((s) => {
      const remaining = s.conversations.filter((c) => !idSet.has(c.id))
      return {
        conversations: remaining,
        activeId: s.activeId && idSet.has(s.activeId) ? remaining[0]?.id ?? null : s.activeId,
      }
    })
  },

  renameConversation: async (id, title) => {
    await renameConversationApi(id, title)
    set((s) => ({
      conversations: s.conversations.map((c) =>
        c.id === id ? { ...c, title } : c
      ),
    }))
  },

  generateConversationTitle: async (id, message, settings) => {
    try {
      const conv = await generateConversationTitleApi(id, message, settings)
      set((s) => ({
        conversations: s.conversations.map((c) =>
          c.id === id ? { ...c, title: conv.title } : c
        ),
      }))
    } catch {
      // Title stays "New Chat" until retry or manual rename
    }
  },

  addMessage: (convId, msg) => {
    set((s) => ({
      conversations: s.conversations.map((c) =>
        c.id === convId
          ? { ...c, messages: [...c.messages, msg], updatedAt: new Date() }
          : c
      ),
    }))
    if (msg.role === 'user') {
      createMessageApi(convId, {
        id: msg.id,
        role: msg.role,
        content: msg.content,
      }).catch(() => {})
    }
  },

  appendChunk: (convId, msgId, chunk) => {
    set((s) => ({
      conversations: s.conversations.map((c) =>
        c.id === convId
          ? {
              ...c,
              messages: c.messages.map((m) =>
                m.id === msgId ? { ...m, content: m.content + chunk } : m
              ),
            }
          : c
      ),
    }))
  },

  replaceContent: (convId, msgId, content) => {
    set((s) => ({
      conversations: s.conversations.map((c) =>
        c.id === convId
          ? { ...c, messages: c.messages.map((m) => (m.id === msgId ? { ...m, content } : m)) }
          : c
      ),
    }))
  },

  finalizeMessage: async (convId, msgId, agentName?, error?) => {
    const conv = get().conversations.find((c) => c.id === convId)
    const msg = conv?.messages.find((m) => m.id === msgId)
    const content = msg?.content ?? ''
    const agent = agentName ?? msg?.agentName

    set((s) => ({
      conversations: s.conversations.map((c) =>
        c.id === convId
          ? {
              ...c,
              messages: c.messages.map((m) =>
                m.id === msgId
                  ? {
                      ...m,
                      isStreaming: false,
                      agentName: agent ?? m.agentName,
                      error: error ?? m.error,
                    }
                  : m
              ),
            }
          : c
      ),
    }))

    if (content) {
      try {
        await updateMessageApi(convId, msgId, content, agent)
      } catch {
        await createMessageApi(convId, {
          id: msgId,
          role: 'assistant',
          content,
          agentName: agent,
        })
      }
    }
  },

  editMessageAndTruncate: async (convId, msgId, content) => {
    set((s) => ({
      conversations: truncateMessagesAfter(s.conversations, convId, msgId, content),
    }))
    try {
      const conv = await editMessageAndTruncateApi(convId, msgId, content)
      set((s) => ({
        conversations: s.conversations.map((c) => (c.id === convId ? conv : c)),
      }))
    } catch (err) {
      await get().loadConversations()
      throw err
    }
  },

  setGenerating: (val) => set({ isGenerating: val }),

  clearAllConversations: async () => {
    await clearAllConversationsApi()
    set({ conversations: [], activeId: null })
  },

  queueAutoSend: (convId, text) => set({ pendingAutoSend: { convId, text } }),

  consumePendingAutoSend: () => {
    const pending = get().pendingAutoSend
    if (pending) set({ pendingAutoSend: null })
    return pending
  },

  setPendingStarterPrompt: (starter) => set({ pendingStarterPrompt: starter }),

  consumePendingStarterPrompt: () => {
    const text = get().pendingStarterPrompt
    if (text) set({ pendingStarterPrompt: null })
    return text
  },
}))
