'use client'

import { useRef, useState } from 'react'
import { nanoid } from 'nanoid'
import { toast } from 'sonner'
import { useChatStore } from '@/store/chatStore'
import { useGitHubAuth } from '@/hooks/useGitHubAuth'
import { chatPreflightApi } from '@/lib/api'
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
    finalizeMessage,
    editMessageAndTruncate,
    setGenerating,
    generateConversationTitle,
  } = useChatStore()
  const { signInWithGitHub } = useGitHubAuth()
  const [oauthPermissionError, setOauthPermissionError] = useState<PermissionError | null>(null)
  const [isReauthing, setIsReauthing] = useState(false)
  const pendingAfterOAuthRef = useRef<PendingOAuthRetry | null>(null)

  const appendUserMessage = async (text: string, convId: string | null) => {
    let targetId = convId
    if (!targetId) {
      throw new Error('Select an agent to start a chat')
    }

    const convBefore = useChatStore.getState().conversations.find((c) => c.id === targetId)
    const isFirstMessage = !convBefore || convBefore.messages.length === 0

    addMessage(targetId, {
      id: nanoid(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    })

    if (isFirstMessage || convBefore?.title === 'New Chat') {
      void generateConversationTitle(targetId, text, settings)
    }

    return targetId
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

    if (!options?.skipUserMessage) {
      await appendUserMessage(text, convId)
    }

    const assistantMsgId = nanoid()
    addMessage(convId, {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      isStreaming: true,
      timestamp: new Date(),
    })
    setGenerating(true)

    const history = buildHistory(convId, Boolean(options?.skipUserMessage))
    await runStream(convId, text, assistantMsgId, history, locked)
  }

  const handleEditResend = async (messageId: string, newText: string) => {
    if (!activeId || isGenerating || chatDisabled || !roomAgent) return

    if (settings.agentOverrides[roomAgent]?.enabled === false) {
      toast.error(`${getAgentLabel(roomAgent)} is disabled in settings`)
      return
    }

    try {
      await editMessageAndTruncate(activeId, messageId, newText)

      const preflight = await chatPreflightApi(
        newText,
        roomAgent,
        settings,
        activeId
      )

      if (!preflight.oauthGranted) {
        pendingAfterOAuthRef.current = {
          text: newText,
          convId: activeId,
          skipUserMessage: true,
        }
        setOauthPermissionError({
          code: 'INSUFFICIENT_SCOPE',
          agent: preflight.agent,
          scope: preflight.scope ?? '',
          label: preflight.label,
          message: `${preflight.label} permission was not granted on GitHub. Re-authenticate to grant access.`,
        })
        return
      }

      if (!preflight.webSearchConfigured) {
        toast.error('Add your Tavily API key in Settings → Web Search')
        return
      }

      await sendMessage(newText, {
        skipUserMessage: true,
        convId: activeId,
      })
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

    const targetId = await appendUserMessage(text, convId)
    const assistantMsgId = nanoid()
    addMessage(targetId, {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      isStreaming: true,
      timestamp: new Date(),
    })
    setGenerating(true)

    try {
      const preflight = await chatPreflightApi(
        text,
        locked,
        settings,
        targetId
      )

      if (!preflight.oauthGranted) {
        pendingAfterOAuthRef.current = {
          text,
          convId: targetId,
          skipUserMessage: true,
        }
        setOauthPermissionError({
          code: 'INSUFFICIENT_SCOPE',
          agent: preflight.agent,
          scope: preflight.scope ?? '',
          label: preflight.label,
          message: `${preflight.label} permission was not granted on GitHub. Re-authenticate to grant access.`,
        })
        await finalizeMessage(
          targetId,
          assistantMsgId,
          preflight.agent as AgentName,
          `${preflight.label} permission was not granted.`
        )
        setGenerating(false)
        return
      }

      if (!preflight.webSearchConfigured) {
        toast.error('Add your Tavily API key in Settings → Web Search')
        await finalizeMessage(
          targetId,
          assistantMsgId,
          'web',
          'Tavily API key is not configured. Add it in Settings → Web Search.'
        )
        setGenerating(false)
        return
      }

      const history = buildHistory(targetId, true)
      setAssistantAgent(targetId, assistantMsgId, preflight.agent as AgentName)
      await runStream(targetId, text, assistantMsgId, history, locked)
    } catch (err) {
      const message = describeStreamFailure(err)
      toast.error(message)
      await finalizeMessage(targetId, assistantMsgId, undefined, message)
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

      const preflight = await chatPreflightApi(
        pending.text,
        roomAgent ?? undefined,
        settings,
        pending.convId
      )

      if (!preflight.oauthGranted) {
        toast.error(`${preflight.label} permission is still not granted`)
        return
      }

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
