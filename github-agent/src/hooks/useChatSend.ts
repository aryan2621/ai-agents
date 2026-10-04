'use client'

import { useRef, useState } from 'react'
import { nanoid } from 'nanoid'
import { toast } from 'sonner'
import { useChatStore } from '@/store/chatStore'
import { useGitHubAuth } from '@/hooks/useGitHubAuth'
import { getAgentLabel, isRoomAgent, type RoomAgentName } from '@/lib/agents'
import { streamChat, describeStreamFailure } from '@/lib/streaming'
import type { AgentName, PermissionError, Settings } from '@/types'

interface PendingOAuthRetry {
  text: string
  convId?: string
  skipUserMessage?: boolean
}

interface UseChatSendArgs {
  activeId: string | null
  roomAgent: RoomAgentName | null
  chatDisabled: boolean
  isGenerating: boolean
  settings: Settings
}

export function useChatSend({
  activeId,
  roomAgent,
  chatDisabled,
  isGenerating,
  settings,
}: UseChatSendArgs) {
  const {
    addMessage,
    appendChunk,
    replaceContent,
    finalizeMessage,
    editMessageAndTruncate,
    setGenerating,
    generateConversationTitle,
    saveDraft,
  } = useChatStore()
  const { signInWithGitHub } = useGitHubAuth()
  const [oauthPermissionError, setOauthPermissionError] = useState<PermissionError | null>(null)
  const [isReauthing, setIsReauthing] = useState(false)
  const pendingAfterOAuthRef = useRef<PendingOAuthRetry | null>(null)

  /** Adds the user's message; returns whether the chat still needs a title. */
  const appendUserMessage = (text: string, convId: string) => {
    const convBefore = useChatStore.getState().conversations.find((c) => c.id === convId)
    addMessage(convId, {
      id: nanoid(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    })
    return !convBefore || convBefore.messages.length === 0 || convBefore.title === 'New Chat'
  }

  const buildHistory = (convId: string, excludeLastUserMessage = false) => {
    const conv = useChatStore.getState().conversations.find((c) => c.id === convId)
    const messages = conv?.messages ?? []
    const slice = excludeLastUserMessage ? messages.slice(0, -1) : messages
    return slice.slice(-20).map((m) => ({
      role: m.role,
      content: m.content,
      ...(m.agentName ? { agent_name: m.agentName } : {}),
    }))
  }

  const setAssistantAgent = (convId: string, msgId: string, agent: AgentName) => {
    useChatStore.setState((s) => ({
      conversations: s.conversations.map((c) =>
        c.id === convId
          ? {
              ...c,
              messages: c.messages.map((m) =>
                m.id === msgId ? { ...m, agentName: agent } : m
              ),
            }
          : c
      ),
    }))
  }

  const runStream = async (
    convId: string,
    text: string,
    assistantMsgId: string,
    history: { role: 'user' | 'assistant' | 'system'; content: string }[],
    agentFilter: string
  ) => {
    let resolvedAgent: AgentName | undefined

    await streamChat({
      message: text,
      conversationId: convId,
      assistantMessageId: assistantMsgId,
      agentFilter,
      history,
      settings,
      onChunk: (chunk, agent) => {
        if (chunk) appendChunk(convId, assistantMsgId, chunk)
        if (agent) {
          resolvedAgent = agent as AgentName
          setAssistantAgent(convId, assistantMsgId, resolvedAgent)
        }
      },
      onReplace: (content) => replaceContent(convId, assistantMsgId, content),
      onDone: async () => {
        const conv = useChatStore.getState().conversations.find((c) => c.id === convId)
        const msg = conv?.messages.find((m) => m.id === assistantMsgId)
        const isEmpty = !msg?.content?.trim()
        await finalizeMessage(
          convId,
          assistantMsgId,
          resolvedAgent,
          isEmpty ? 'No response was generated. Try again or rephrase your request.' : undefined
        )
        setGenerating(false)
      },
      onError: async (err) => {
        toast.error(err)
        await finalizeMessage(convId, assistantMsgId, resolvedAgent, err)
        setGenerating(false)
      },
      onPermissionError: async (err) => {
        pendingAfterOAuthRef.current = {
          text,
          convId,
          skipUserMessage: true,
        }
        setOauthPermissionError(err)
        await finalizeMessage(convId, assistantMsgId, resolvedAgent, err.message)
        setGenerating(false)
      },
    })
  }

  const sendMessage = async (
    text: string,
    options?: {
      skipUserMessage?: boolean
      convId?: string | null
    }
  ) => {
    const convId = options?.convId ?? activeId
    if (!convId) {
      toast.error('Start a new chat first')
      return
    }
    const conv = useChatStore.getState().conversations.find((c) => c.id === convId)
    const locked = isRoomAgent(conv?.agentFilter) ? conv.agentFilter : null
    if (!locked) {
      toast.error('This chat is not tied to an agent. Start a new chat from the home screen.')
      return
    }

    await saveDraft(convId)
    const needsTitle = !options?.skipUserMessage && appendUserMessage(text, convId)

    const assistantMsgId = nanoid()
    addMessage(convId, {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      isStreaming: true,
      timestamp: new Date(),
    })
    setGenerating(true)

    const history = buildHistory(convId, true)
    await runStream(convId, text, assistantMsgId, history, locked)
    // After the reply: the local model answers one request at a time, so a title request
    // sent alongside the message would make the reply wait for it.
    if (needsTitle) void generateConversationTitle(convId, text, settings)
  }

  const handleEditResend = async (messageId: string, newText: string) => {
    if (!activeId || isGenerating || chatDisabled || !roomAgent) return

    if (settings.agentOverrides[roomAgent]?.enabled === false) {
      toast.error(`${getAgentLabel(roomAgent)} is disabled in settings`)
      return
    }

    try {
      await editMessageAndTruncate(activeId, messageId, newText)
      await sendMessage(newText, { skipUserMessage: true, convId: activeId })
    } catch (err) {
      toast.error(describeStreamFailure(err))
    }
  }

  const handleSend = async (text: string, existingConvId?: string) => {
    if (chatDisabled || oauthPermissionError) return

    const convId = existingConvId ?? activeId
    const conv = useChatStore.getState().conversations.find((c) => c.id === convId)
    const locked = isRoomAgent(conv?.agentFilter) ? conv.agentFilter : roomAgent
    if (!locked) {
      toast.error('Select an agent to start a chat')
      return
    }

    if (settings.agentOverrides[locked]?.enabled === false) {
      toast.error(`${getAgentLabel(locked)} is disabled in settings`)
      return
    }

    if (!convId) {
      toast.error('Start a new chat first')
      return
    }
    try {
      await sendMessage(text, { convId })
    } catch (err) {
      toast.error(describeStreamFailure(err))
      setGenerating(false)
    }
  }

  const handleGrantOAuthPermission = async () => {
    setIsReauthing(true)
    try {
      await signInWithGitHub({
        navigate: false,
        successMessage: 'Permissions updated',
      })
      setOauthPermissionError(null)
      const pending = pendingAfterOAuthRef.current
      pendingAfterOAuthRef.current = null
      if (!pending) return

      await sendMessage(pending.text, {
        skipUserMessage: pending.skipUserMessage,
        convId: pending.convId,
      })
    } catch {
      toast.error('Failed to update permissions')
    } finally {
      setIsReauthing(false)
    }
  }

  const cancelPendingOAuth = () => {
    setOauthPermissionError(null)
    pendingAfterOAuthRef.current = null
  }

  return {
    handleSend,
    handleEditResend,
    handleGrantOAuthPermission,
    cancelPendingOAuth,
    oauthPermissionError,
    isReauthing,
  }
}
