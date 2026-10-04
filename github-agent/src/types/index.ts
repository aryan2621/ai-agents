export interface PermissionStatus {
  id: string
  label: string
  scope: string
  granted: boolean
}

export interface GitHubUser {
  id: string
  email: string
  name: string
  picture: string
  accessToken: string
  expiresAt: number
  grantedScopes?: string[]
  permissions?: PermissionStatus[]
}

export interface PermissionError {
  code: 'INSUFFICIENT_SCOPE'
  agent: string
  scope: string
  label: string
  message: string
}

export type AgentName =
  | 'repos'
  | 'issues'
  | 'pulls'
  | 'code'
  | 'notifications'
  | 'web'

export type RoomAgentName = AgentName

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  agentName?: AgentName
  timestamp: Date
  isStreaming?: boolean
  error?: string
}

export interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
  updatedAt: Date
  agentFilter?: AgentName | 'all' | string
  /** Opened from the agent picker but not saved yet: it's saved with its first message. */
  draft?: boolean
}

export type ThemeMode = 'light' | 'dark' | 'system'

export interface ReadinessIssue {
  code: string
  message: string
  remediation: string
}

export interface HealthStatus {
  status: string
  ready: boolean
  issues: ReadinessIssue[]
  checks: Record<string, string>
  oauthConfigured?: boolean
  llmConfigured?: boolean
}

/** A built-in AI model (llama.cpp, runs on this Mac). */
export interface LocalModel {
  id: string
  name: string
  note: string
  sizeMb: number
  minRamGb: number
  installed: boolean
}

export interface ModelCatalog {
  ramGb: number
  recommended: string
  running: string | null
  download: { id: string; done: number; total: number; error: string; finished: boolean } | null
  models: LocalModel[]
}

export interface Settings {
  defaultModel: string
  temperature: number
  maxTokens: number
  sendOnEnter: boolean
  autoScroll: boolean
  fontSize: 'sm' | 'md' | 'lg'
  theme: ThemeMode
  onboardingCompleted: boolean
  tavilySearchApiKey: string
  agentOverrides: Record<AgentName, { enabled: boolean }>
}

export interface PendingStarter {
  text: string
  agent: AgentName
}
