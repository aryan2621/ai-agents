import type { AgentName } from '@/types'

export type RoomAgentName = AgentName

export const AGENT_LABELS: Record<AgentName, string> = {
  gmail: 'Gmail',
  calendar: 'Google Calendar',
  drive: 'Google Drive',
  docs: 'Google Docs',
  sheets: 'Google Sheets',
  web: 'Web Search',
}

export const ROOM_AGENT_NAMES: RoomAgentName[] = [
  'gmail',
  'calendar',
  'drive',
  'docs',
  'sheets',
  'web',
]

export const ROOM_AGENTS: {
  id: RoomAgentName
  label: string
  description: string
  includesWeb: boolean
}[] = [
  {
    id: 'gmail',
    label: 'Gmail',
    description: 'Inbox, send, drafts, and replies. Web search included.',
    includesWeb: true,
  },
  {
    id: 'calendar',
    label: 'Calendar',
    description: 'Events, free/busy, and invites. Web search included.',
    includesWeb: true,
  },
  {
    id: 'drive',
    label: 'Drive',
    description: 'Files, folders, and sharing. Web search included.',
    includesWeb: true,
  },
  {
    id: 'docs',
    label: 'Docs',
    description: 'Create and edit Google Docs. Web search included.',
    includesWeb: true,
  },
  {
    id: 'sheets',
    label: 'Sheets',
    description: 'Spreadsheets and tables. Web search included.',
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
