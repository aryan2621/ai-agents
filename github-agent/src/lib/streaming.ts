'use client'

import { useAuthStore } from '@/store/authStore'
import { API_BASE_URL, authHeaders } from '@/lib/config'
import type { PermissionError, Settings } from '@/types'

let activeAbortController: AbortController | null = null

export function describeStreamFailure(err: unknown): string {
  const message = err instanceof Error ? err.message : String(err)
  if (
    message === 'Load failed' ||
    message === 'Failed to fetch' ||
    message.toLowerCase().includes('networkerror')
  ) {
    return 'Could not reach the backend. Check the Python server terminal for errors, then try again.'
  }
  return message || 'Stream failed'
}

export function cancelActiveStream() {
  activeAbortController?.abort()
  activeAbortController = null
}

interface StreamChunk {
  chunk?: string
  agent?: string
  agents?: string[]
  phase?: 'executing' | 'synthesizing'
  done?: boolean
  error?: string
  code?: string
  scope?: string
  label?: string
}

interface HistoryMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  agent_name?: string
}

export async function streamChat(params: {
  message: string
  conversationId: string
  assistantMessageId?: string
  agentFilter?: string
  history?: HistoryMessage[]
  settings?: Settings
  signal?: AbortSignal
  onChunk: (text: string, agent?: string) => void
  onDone: () => void
  onError: (err: string) => void
  onPermissionError?: (err: PermissionError) => void
}) {
  const { user } = useAuthStore.getState()

  const body: Record<string, unknown> = {
    message: params.message,
    conversation_id: params.conversationId,
    agent_filter: params.agentFilter,
    assistant_message_id: params.assistantMessageId ?? null,
  }

  if (params.history?.length) {
    body.history = params.history
  }

  if (params.settings) {
    body.settings = {
      default_model: params.settings.defaultModel,
      temperature: params.settings.temperature,
      max_tokens: params.settings.maxTokens,
      agent_overrides: params.settings.agentOverrides,
      ollama_base_url: params.settings.ollamaBaseUrl,
    }
  }

  const controller = new AbortController()
  activeAbortController = controller
  const signal = params.signal ?? controller.signal

  try {
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: authHeaders(user?.accessToken),
      body: JSON.stringify(body),
      signal,
    })

    if (!response.ok || !response.body) {
      params.onError(`Backend error: ${response.status}`)
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const raw = line.slice(6).trim()
        if (raw === '[DONE]') {
          params.onDone()
          return
        }
        try {
          const parsed: StreamChunk = JSON.parse(raw)
          if (parsed.code === 'INSUFFICIENT_SCOPE' && params.onPermissionError) {
            params.onPermissionError({
              code: parsed.code,
              agent: parsed.agent ?? '',
              scope: parsed.scope ?? '',
              label: parsed.label ?? 'GitHub',
              message: parsed.error ?? 'Permission required',
            })
            return
          }
          if (parsed.error) {
            params.onError(parsed.error)
            return
          }
          if (parsed.chunk) params.onChunk(parsed.chunk, parsed.agent)
          if (parsed.agent && !parsed.chunk && !parsed.phase) {
            params.onChunk('', parsed.agent)
          }
        } catch {
          // skip malformed SSE lines
        }
      }
    }

    params.onDone()
  } catch (err) {
    if (signal.aborted) {
      params.onError('Generation stopped')
      return
    }
    params.onError(describeStreamFailure(err))
  } finally {
    if (activeAbortController === controller) {
      activeAbortController = null
    }
  }
}
