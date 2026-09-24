export interface PermissionStatus {
  id: string
  label: string
  scope: string
  granted: boolean
}

export interface GoogleUser {
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
  | 'gmail'
  | 'calendar'
  | 'drive'
  | 'docs'
  | 'sheets'
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
  ollamaConfigured?: boolean
  ollamaBaseUrl?: string
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
  ollamaBaseUrl: string
  agentOverrides: Record<AgentName, { enabled: boolean }>
}

export interface PendingStarter {
  text: string
  agent: AgentName
}

