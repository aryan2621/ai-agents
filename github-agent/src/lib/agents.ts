import type { AgentName } from '@/types'

export type RoomAgentName = AgentName

export const AGENT_LABELS: Record<AgentName, string> = {
  repos: 'Repos',
  issues: 'Issues',
  pulls: 'Pull requests',
  code: 'Code',
  notifications: 'Notifications',
  web: 'Web Search',
}

export const ROOM_AGENT_NAMES: RoomAgentName[] = [
  'repos',
  'issues',
  'pulls',
  'code',
  'notifications',
  'web',
]

export const ROOM_AGENTS: {
  id: RoomAgentName
  label: string
  description: string
  includesWeb: boolean
}[] = [
  {
    id: 'repos',
    label: 'Repos',
    description: 'List, search, and inspect repositories. Web search included.',
    includesWeb: true,
  },
  {
    id: 'issues',
    label: 'Issues',
    description: 'Assigned issues, comments, and tracking. Web search included.',
    includesWeb: true,
  },
  {
    id: 'pulls',
    label: 'Pull requests',
    description: 'Open PRs, reviews, and merges. Web search included.',
    includesWeb: true,
  },
  {
    id: 'code',
    label: 'Code',
    description: 'Files, search, and commits. Web search included.',
    includesWeb: true,
  },
  {
    id: 'notifications',
    label: 'Notifications',
    description: 'Unread GitHub notifications. Web search included.',
    includesWeb: true,
  },
  {
    id: 'web',
    label: 'Web Search',
    description: 'Public internet research only.',
    includesWeb: false,
  },
]

export function isRoomAgent(agent?: string | null): agent is RoomAgentName {
  return ROOM_AGENT_NAMES.includes(agent as RoomAgentName)
}

export function getAgentLabel(agent?: AgentName | string | null): string | null {
  if (!agent) return null
  return AGENT_LABELS[agent as AgentName] ?? String(agent)
}
