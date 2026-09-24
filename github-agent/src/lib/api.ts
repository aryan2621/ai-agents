import ky, { type KyInstance } from 'ky'
import { useAuthStore } from '@/store/authStore'
import { API_BASE_URL } from '@/lib/config'
import type {
  Conversation,
  GitHubUser,
  HealthStatus,
  ReadinessIssue,
  Settings,
} from '@/types'

/** Preflight runs LLM routing; local Ollama inference can exceed ky's 10s default. */
const LLM_API_TIMEOUT_MS = 60_000

const api: KyInstance = ky.create({
  prefixUrl: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  hooks: {
    beforeRequest: [
      (request) => {
        const { user } = useAuthStore.getState()
        if (user?.accessToken) {
          request.headers.set('Authorization', `Bearer ${user.accessToken}`)
        }
      },
    ],
  },
})

export async function fetchHealth(): Promise<HealthStatus> {
  const { user } = useAuthStore.getState()
  const headers: Record<string, string> = {}
  if (user?.accessToken) {
    headers.Authorization = `Bearer ${user.accessToken}`
  }
  const data = await ky
    .get(`${API_BASE_URL}/health`, { timeout: 5000, headers })
    .json<Record<string, unknown>>()

  const checks = (data.checks ?? {}) as Record<string, string>
  const issues = Array.isArray(data.issues)
    ? (data.issues as HealthStatus['issues'])
    : buildIssuesFromChecks(checks)

  return {
    status: String(data.status ?? (issues.length === 0 ? 'ok' : 'degraded')),
    ready: typeof data.ready === 'boolean' ? data.ready : issues.length === 0,
    issues,
    checks,
    oauthConfigured: Boolean(data.oauth_configured ?? data.oauthConfigured),
    llmConfigured: Boolean(data.llm_configured ?? data.llmConfigured),
    ollamaConfigured: Boolean(data.ollama_configured ?? data.ollamaConfigured),
    ollamaBaseUrl: String(data.ollama_base_url ?? data.ollamaBaseUrl ?? ''),
  }
}

function buildIssuesFromChecks(checks: Record<string, string>): ReadinessIssue[] {
  const issues: ReadinessIssue[] = []
  if (checks.database === 'error') {
    issues.push({
      code: 'database',
      message: 'Database is not available.',
      remediation: 'Restart the app. SQLite is used by default; set DATABASE_URL for PostgreSQL.',
    })
  }
  if (checks.network === 'error') {
    issues.push({
      code: 'network',
      message: 'No internet connection.',
      remediation: 'Connect to the internet — GitHub requires network access.',
    })
  }
  if (checks.llm === 'error') {
    issues.push({
      code: 'llm',
      message: 'Ollama is not running.',
      remediation: 'Start Ollama and pull a model (ollama pull ministral-3:8b).',
    })
  }
  return issues
}

export async function chatPreflightApi(
  message: string,
  agentFilter?: string,
  settings?: Settings,
  conversationId?: string
): Promise<{
  agent: string
  label: string
  agents?: string[]
  oauthGranted: boolean
  scope?: string
  webSearchConfigured: boolean
}> {
  const body: Record<string, unknown> = { message, agent_filter: agentFilter }
  if (conversationId) {
    body.conversation_id = conversationId
  }
  if (settings) {
    body.settings = {
      default_model: settings.defaultModel,
      temperature: settings.temperature,
      max_tokens: settings.maxTokens,
      agent_overrides: settings.agentOverrides,
    }
  }
  try {
    const data = await api
      .post('chat/preflight', { json: body, timeout: 15_000 })
      .json<{
      agent: string
      label: string
      agents?: string[]
      oauth_granted: boolean
      scope?: string
      web_search_configured?: boolean
    }>()
    return {
      agent: data.agent,
      label: data.label,
      agents: data.agents,
      oauthGranted: data.oauth_granted,
      scope: data.scope,
      webSearchConfigured: data.web_search_configured ?? true,
    }
  } catch (err) {
    const kyErr = err as { response?: Response; message?: string }
    if (kyErr.response) {
      let detail = ''
      try {
        const payload = (await kyErr.response.json()) as { detail?: unknown }
        detail = typeof payload.detail === 'string' ? payload.detail : ''
      } catch {
        detail = ''
      }
      throw new Error(detail || `Backend error: ${kyErr.response.status}`)
    }
    throw new Error(
      kyErr.message === 'Load failed' || kyErr.message === 'Failed to fetch'
        ? 'Could not reach the backend. Check the Python server terminal for errors, then try again.'
        : kyErr.message || 'Failed to prepare action'
    )
  }
}

/** Poll until the Python backend responds on /health (sidecar may still be starting). */
export async function waitForBackend(maxWaitMs = 90_000): Promise<boolean> {
  const deadline = Date.now() + maxWaitMs
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        signal: AbortSignal.timeout(2000),
      })
      if (response.ok) return true
    } catch {
      // backend not up yet
    }
    await new Promise((resolve) => setTimeout(resolve, 500))
  }
  return false
}

export async function fetchMe(accessToken?: string): Promise<GitHubUser> {
  const token = accessToken ?? useAuthStore.getState().user?.accessToken
  const headers: Record<string, string> = {}
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  return ky.get(`${API_BASE_URL}/auth/me`, { headers }).json<GitHubUser>()
}

export async function logout(): Promise<void> {
  await api.post('auth/logout')
}

export async function transcribeAudioApi(blob: Blob): Promise<{ text: string }> {
  const form = new FormData()
  form.append('audio', blob, 'recording.wav')
  const { user } = useAuthStore.getState()
  const headers: Record<string, string> = {}
  if (user?.accessToken) {
    headers.Authorization = `Bearer ${user.accessToken}`
  }
  return ky
    .post(`${API_BASE_URL}/speech/transcribe`, {
      body: form,
      headers,
      timeout: LLM_API_TIMEOUT_MS,
    })
    .json<{ text: string }>()
}

export async function fetchConversations(): Promise<Conversation[]> {
  const data = await api.get('conversations').json<Conversation[]>()
  return data.map(reviveConversation)
}

export async function fetchConversationApi(id: string): Promise<Conversation> {
  const data = await api.get(`conversations/${id}`).json<Conversation>()
  return reviveConversation(data)
}

export async function createConversationApi(
  id: string,
  agentFilter: string,
  title = 'New Chat'
): Promise<Conversation> {
  const data = await api
    .post('conversations', { json: { id, title, agentFilter } })
    .json<Conversation>()
  return reviveConversation(data)
}

export async function renameConversationApi(id: string, title: string): Promise<void> {
  await api.patch(`conversations/${id}`, { json: { title } })
}

export async function generateConversationTitleApi(
  convId: string,
  message: string,
  settings?: Settings
): Promise<Conversation> {
  const body: Record<string, unknown> = { message }
  if (settings) {
    body.settings = {
      default_model: settings.defaultModel,
      temperature: settings.temperature,
      max_tokens: settings.maxTokens,
      agent_overrides: settings.agentOverrides,
    }
  }
  const data = await api
    .post(`conversations/${convId}/generate-title`, { json: body })
    .json<Conversation>()
  return reviveConversation(data)
}

export async function deleteConversationApi(id: string): Promise<void> {
  await api.delete(`conversations/${id}`)
}

export async function deleteConversationsApi(ids: string[]): Promise<number> {
  const data = await api
    .post('conversations/bulk-delete', { json: { ids } })
    .json<{ deleted: number }>()
  return data.deleted
}

export async function clearAllConversationsApi(): Promise<void> {
  await api.delete('conversations')
}

export async function createMessageApi(
  convId: string,
  msg: { id: string; role: string; content: string; agentName?: string }
): Promise<void> {
  await api.post(`conversations/${convId}/messages`, { json: msg })
}

export async function updateMessageApi(
  convId: string,
  msgId: string,
  content: string,
  agentName?: string
): Promise<void> {
  await api.patch(`conversations/${convId}/messages/${msgId}`, { json: { content, agentName } })
}

export async function editMessageAndTruncateApi(
  convId: string,
  msgId: string,
  content: string
): Promise<Conversation> {
  const data = await api
    .post(`conversations/${convId}/messages/${msgId}/edit`, { json: { content } })
    .json<Conversation>()
  return reviveConversation(data)
}

export async function fetchSettings(): Promise<Settings> {
  const raw = await api.get('settings').json<Record<string, unknown>>()
  return parseSettings(raw)
}

export async function updateSettingsApi(patch: Partial<Settings>): Promise<Settings> {
  const raw = await api.put('settings', { json: patch }).json<Record<string, unknown>>()
  return parseSettings(raw)
}

export async function fetchOAuthSetupStatus(): Promise<{ configured: boolean; clientIdPreview: string }> {
  const data = await ky.get(`${API_BASE_URL}/setup/oauth/status`, { timeout: 5000 }).json<{
    configured: boolean
    clientIdPreview: string
  }>()
  return data
}

export async function saveOAuthCredentials(clientId: string, clientSecret: string): Promise<void> {
  await ky.post(`${API_BASE_URL}/setup/oauth`, {
    json: { clientId, clientSecret },
    timeout: 10_000,
  })
}

export async function fetchLlmSetupStatus(): Promise<{
  configured: boolean
  ollamaConfigured: boolean
  ollamaBaseUrl: string
}> {
  return ky.get(`${API_BASE_URL}/setup/llm/status`, { timeout: 5000 }).json()
}

export async function saveLlmCredentials(
  ollamaBaseUrl = '',
  defaultModel = ''
): Promise<void> {
  await ky.post(`${API_BASE_URL}/setup/llm`, {
    json: { ollamaBaseUrl, defaultModel },
    timeout: 10_000,
  })
}

function parseSettings(raw: Record<string, unknown>): Settings {
  const agentOverrides = (raw.agentOverrides ?? raw.agent_overrides ?? {}) as Settings['agentOverrides']
  return {
    defaultModel: String(raw.defaultModel ?? raw.default_model ?? 'ministral-3:8b'),
    temperature: Number(raw.temperature ?? 0.7),
    maxTokens: Number(raw.maxTokens ?? raw.max_tokens ?? 2048),
    sendOnEnter: Boolean(raw.sendOnEnter ?? raw.send_on_enter ?? true),
    autoScroll: Boolean(raw.autoScroll ?? raw.auto_scroll ?? true),
    fontSize: (raw.fontSize ?? raw.font_size ?? 'md') as Settings['fontSize'],
    theme: (raw.theme ?? 'system') as Settings['theme'],
    onboardingCompleted: Boolean(raw.onboardingCompleted ?? raw.onboarding_completed ?? false),
    tavilySearchApiKey: String(
      raw.tavilySearchApiKey ?? raw.tavily_search_api_key ?? raw.braveSearchApiKey ?? raw.brave_search_api_key ?? ''
    ),
    ollamaBaseUrl: String(raw.ollamaBaseUrl ?? raw.ollama_base_url ?? 'http://127.0.0.1:11434'),
    agentOverrides,
  }
}

function reviveConversation(raw: Conversation): Conversation {
  return {
    ...raw,
    createdAt: new Date(raw.createdAt),
    updatedAt: new Date(raw.updatedAt),
    messages: (raw.messages ?? []).map((m) => ({
      ...m,
      timestamp: new Date(m.timestamp),
    })),
  }
}
